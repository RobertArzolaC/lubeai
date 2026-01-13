import logging
from pathlib import Path
from typing import Dict

import polars as pl
from celery import shared_task

from apps.etl import exceptions, utils
from apps.reports import models as report_models
from apps.reports.services import bulk_upload
from apps.users import models as user_models

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=300,  # 5 minutes
)
def download_intertek_report_task(
    self,
    search_text: str = "",
    lab_number: str = "",
    page_size: int = 50,
    file_type: int = 3,
) -> Dict[str, str]:
    """
    Celery task to download Intertek inspection report.

    Args:
        self: Task instance (bound task).
        search_text: Text to search for in reports.
        lab_number: Laboratory number to filter by.
        page_size: Number of records per page.
        file_type: Export file type (1=CSV, 2=PDF, 3=Excel).

    Returns:
        Dictionary with download status and file path.

    Raises:
        Exception: If download fails after retries.
    """
    logger.info(
        f"Starting Intertek report download task (task_id: {self.request.id})"
    )

    client = None

    try:
        # Get configured API client
        client = utils.get_intertek_client()

        # Download report
        file_path = client.download_inspection_report(
            search_text=search_text,
            lab_number=lab_number,
            page_size=page_size,
            file_type=file_type,
        )

        logger.info(f"Report downloaded successfully: {file_path}")

        return {
            "status": "success",
            "file_path": str(file_path),
            "file_size": file_path.stat().st_size,
        }

    except exceptions.ETLException as e:
        logger.error(f"ETL error in download task: {e}")

        # Retry on authentication or API errors
        if isinstance(
            e, (exceptions.AuthenticationError, exceptions.APIRequestError)
        ):
            logger.info(f"Retrying task (attempt {self.request.retries + 1})")
            raise self.retry(exc=e)

        # Don't retry on configuration errors
        return {"status": "error", "error": str(e)}

    except Exception as e:
        logger.error(f"Unexpected error in download task: {e}")
        raise self.retry(exc=e)

    finally:
        if client:
            client.close()


@shared_task
def process_report_task(file_path: str) -> Dict[str, str]:
    """
    Celery task to process downloaded inspection report with incremental loading.

    Implements incremental loading based on sample_date filtering. Only processes
    records with sample_date > last existing report in database. Uses polars for
    high-performance data filtering and bulk_create() for batch operations.

    Args:
        file_path: Path to the downloaded report file.

    Returns:
        Dictionary with processing status and results.
    """

    logger.info(f"Starting ETL report processing: {file_path}")
    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return {"status": "error", "error": "File not found"}

    try:
        # Get or create system user for ETL operations
        system_user, created = user_models.User.objects.get_or_create(
            email="system@lubeai.com",
            defaults={
                "first_name": "System",
                "last_name": "ETL",
                "is_active": True,
                "is_staff": False,
            },
        )

        if created:
            logger.info("Created system user for ETL operations")

        # Load DataFrame with polars
        logger.info(f"Loading Excel file with polars: {path}")
        df = pl.read_excel(path)

        # Skip title and header row (rows 0-1)
        df = df.slice(1)

        # Select only the first 57 columns (0-56) to exclude blank columns
        if df.width > 57:
            extra_cols = df.width - 57
            df = df.select(df.columns[:57])
            logger.debug(
                f"Selected first 57 columns, excluded {extra_cols} blank columns"
            )

        logger.info(f"Loaded {len(df)} rows from Excel file")

        # Get last sample_date from database
        last_report = (
            report_models.Report.objects.filter(sample_date__isnull=False)
            .order_by("-sample_date")
            .only("sample_date")
            .first()
        )

        # Filter incremental data
        total_rows = len(df)

        if last_report:
            logger.info(
                f"Last sample_date in database: {last_report.sample_date}"
            )

            # Rename columns for easier access
            df = df.rename(
                {col: f"column_{i}" for i, col in enumerate(df.columns)}
            )

            # Parse sample_date column (column_7) and filter
            df = df.with_columns(
                [
                    pl.col("column_7")
                    .map_elements(
                        lambda x: utils.parse_polars_date(x),
                        return_dtype=pl.Date,
                    )
                    .alias("parsed_sample_date")
                ]
            )

            # Filter records where sample_date > last_sample_date
            df = df.filter(
                pl.col("parsed_sample_date") > last_report.sample_date
            )

            # Drop the temporary parsed_sample_date column
            df = df.drop("parsed_sample_date")

            filtered_rows = len(df)
            logger.info(
                f"Incremental filter: {filtered_rows}/{total_rows} rows "
                f"(sample_date > {last_report.sample_date})"
            )
        else:
            logger.info(
                "First load - no existing reports, processing all records"
            )
            filtered_rows = total_rows

        if len(df) == 0:
            logger.info("No new records to process after filtering")
            return {
                "status": "success",
                "results": {
                    "created": 0,
                    "updated": 0,
                    "skipped": 0,
                    "errors": [],
                },
                "total_rows": total_rows,
                "filtered_rows": 0,
            }

        # Process with bulk upload service
        logger.info("Processing DataFrame with ReportBulkUploadService")
        service = bulk_upload.ReportBulkUploadService(user=system_user)
        results = service.process_dataframe(df)

        logger.info(
            f"ETL completed: {results['created']} created, "
            f"{results['skipped']} skipped, {len(results['errors'])} errors"
        )

        # Determine status
        if results["errors"]:
            status = "partial_success" if results["created"] > 0 else "error"
        else:
            status = "success"

        return {
            "status": status,
            "results": results,
            "total_rows": total_rows,
            "filtered_rows": filtered_rows,
        }

    except Exception as e:
        logger.exception(f"Fatal error in ETL processing: {e}")
        return {
            "status": "error",
            "error": str(e),
            "file_path": str(path),
        }

    finally:
        # Clean up temporary file
        if path.exists():
            try:
                path.unlink()
                logger.info(f"Temp file cleaned up: {path}")
            except Exception as e:
                logger.error(f"Failed to clean up temp file: {e}")


@shared_task
def download_and_process_report_task(
    search_text: str = "",
    lab_number: str = "",
    page_size: int = 50,
    file_type: int = 3,
) -> Dict[str, str]:
    """
    Celery task to download and process Intertek report in one workflow.

    This task chains the download and processing steps together.

    Args:
        search_text: Text to search for in reports.
        lab_number: Laboratory number to filter by.
        page_size: Number of records per page.
        file_type: Export file type (1=CSV, 2=PDF, 3=Excel).

    Returns:
        Dictionary with workflow status.
    """
    logger.info("Starting download and process workflow")

    # Download report
    download_result = download_intertek_report_task(
        search_text=search_text,
        lab_number=lab_number,
        page_size=page_size,
        file_type=file_type,
    )

    if download_result.get("status") != "success":
        logger.error("Download failed, aborting processing")
        return download_result

    # Process downloaded report
    file_path = download_result.get("file_path")
    process_result = process_report_task(file_path)

    logger.info("Download and process workflow completed")

    return {
        "status": "success",
        "download_result": download_result,
        "process_result": process_result,
    }
