from datetime import datetime

from constance import config
from django.utils.dateparse import parse_date

from apps.etl import exceptions
from apps.etl.services import IntertekAPIClient


def get_intertek_client() -> IntertekAPIClient:
    """
    Get configured Intertek API client instance.

    Retrieves credentials from django-constance configuration and
    returns an initialized API client.

    Returns:
        Configured IntertekAPIClient instance.

    Raises:
        ETLException: If API integration is disabled or credentials are missing.
    """
    if not config.INTERTEK_API_ENABLED:
        raise exceptions.ETLException("Intertek API integration is disabled")

    username = config.INTERTEK_API_USERNAME
    password = config.INTERTEK_API_PASSWORD

    if not username or not password:
        raise exceptions.ETLException("Intertek API credentials not configured")

    return IntertekAPIClient(username=username, password=password)


def parse_polars_date(date_value):
    """
    Parse date value for polars.

    This is a helper function for use in polars map_elements. It returns
    None for unparseable dates so they can be filtered out.

    Args:
        date_value: Date value to parse.

    Returns:
        Parsed date or None.
    """
    if not date_value:
        return None

    # Convert to string if it's not already
    date_str = str(date_value).strip()

    # Handle common date formats
    date_formats = [
        "%d/%m/%Y",  # 18/12/2025
        "%d-%m-%Y",  # 18-12-2025
        "%Y-%m-%d",  # 2025-12-18 (ISO format)
        "%m/%d/%Y",  # 12/18/2025 (US format)
    ]

    for date_format in date_formats:
        try:
            parsed_datetime = datetime.strptime(date_str, date_format)
            return parsed_datetime.date()
        except (ValueError, TypeError):
            continue

    # Try Django's built-in parser as fallback
    try:
        parsed_date = parse_date(date_str)
        if parsed_date:
            return parsed_date
    except Exception:
        pass

    return None
