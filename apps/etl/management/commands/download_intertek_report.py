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

        self.stdout.write("Connecting to Intertek API...")

        try:
            # Get configured API client
            client = utils.get_intertek_client()

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
