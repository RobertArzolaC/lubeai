from constance import config

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
