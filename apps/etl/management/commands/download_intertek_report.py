"""
Management command to download Intertek inspection reports.

This command demonstrates how to use the IntertekAPIClient service
to download inspection detail reports from the Intertek OILCM API.
"""

import logging

from django.core.management.base import BaseCommand, CommandError

from apps.etl import exceptions, utils

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Download Intertek inspection detail report."""

    help = "Download inspection detail report from Intertek OILCM API"

    def add_arguments(self, parser) -> None:
        """
        Add command-line arguments.

        Args:
            parser: Argument parser instance.
        """
        parser.add_argument(
            "--search-text",
            type=str,
            default="",
            help="Text to search for in reports",
        )
        parser.add_argument(
            "--lab-number",
            type=str,
            default="",
            help="Laboratory number to filter by",
        )
        parser.add_argument(
            "--page-size",
            type=int,
            default=50,
            help="Number of records per page (default: 50)",
        )
        parser.add_argument(
            "--file-type",
            type=int,
            default=3,
            choices=[1, 2, 3],
            help="Export file type: 1=CSV, 2=PDF, 3=Excel (default: 3)",
        )
        parser.add_argument(
            "--list",
            action="store_true",
            help="List inspection details as JSON instead of downloading file",
        )

    def handle(self, *args, **options) -> None:
        """
        Execute the command.

        Args:
            *args: Positional arguments.
            **options: Command options.

        Raises:
            CommandError: If download fails or API is not configured.
        """
        search_text = options["search_text"]
        lab_number = options["lab_number"]
        page_size = options["page_size"]
        file_type = options["file_type"]
        list_only = options["list"]

        self.stdout.write("Connecting to Intertek API...")

        try:
            # Get configured API client
            client = utils.get_intertek_client()

            if list_only:
                # Fetch inspection details as JSON
                self.stdout.write("Fetching inspection details...")

                data = client.get_inspection_details(
                    search_text=search_text,
                    lab_number=lab_number,
                    page_size=page_size,
                )

                # Display results
                if data.get("success"):
                    records = data.get("data", [])
                    total = data.get("totalRecords", 0)

                    self.stdout.write(
                        self.style.SUCCESS(
                            f"\nFound {total} records, showing {len(records)}:"
                        )
                    )

                    for record in records:
                        lab_num = record.get("labNumber", "N/A")
                        client_name = record.get("clientName", "N/A")
                        sample_date = record.get("sampleDate", "N/A")

                        self.stdout.write(
                            f"  - Lab: {lab_num} | Client: {client_name} | Date: {sample_date}"
                        )
                else:
                    message = data.get("message", "Unknown error")
                    raise CommandError(f"API request failed: {message}")

            else:
                # Download inspection report file
                self.stdout.write("Downloading inspection report...")

                file_path = client.download_inspection_report(
                    search_text=search_text,
                    lab_number=lab_number,
                    page_size=page_size,
                    file_type=file_type,
                )

                self.stdout.write(
                    self.style.SUCCESS(
                        f"\nReport downloaded successfully to:\n{file_path}"
                    )
                )

                # Display file info
                file_size = file_path.stat().st_size
                self.stdout.write(f"File size: {file_size:,} bytes")

            # Close client connection
            client.close()

        except exceptions.ETLException as e:
            logger.error(f"ETL error: {e}")
            raise CommandError(f"ETL operation failed: {str(e)}") from e

        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise CommandError(f"Unexpected error: {str(e)}") from e
