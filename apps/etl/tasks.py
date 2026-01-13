import logging
from pathlib import Path
from typing import Dict

from celery import shared_task

from apps.etl import exceptions, utils

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
def process_downloaded_report_task(file_path: str) -> Dict[str, str]:
    """
    Celery task to process a downloaded inspection report.

    This is a placeholder task that can be extended to process
    the downloaded files (parse, validate, import to database, etc.).

    Args:
        file_path: Path to the downloaded report file.

    Returns:
        Dictionary with processing status.
    """
    logger.info(f"Starting report processing task for file: {file_path}")

    path = Path(file_path)

    if not path.exists():
        logger.error(f"File not found: {file_path}")
        return {"status": "error", "error": "File not found"}

    try:
        # TODO: Implement report processing logic
        # - Parse Excel/CSV file
        # - Validate data
        # - Import to database
        # - Clean up temporary file

        logger.info("Report processing completed successfully")

        return {
            "status": "success",
            "file_path": str(path),
            "records_processed": 0,  # TODO: Update with actual count
        }

    except Exception as e:
        logger.error(f"Error processing report: {e}")
        return {"status": "error", "error": str(e)}


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
    process_result = process_downloaded_report_task(file_path)

    logger.info("Download and process workflow completed")

    return {
        "status": "success",
        "download_result": download_result,
        "process_result": process_result,
    }
