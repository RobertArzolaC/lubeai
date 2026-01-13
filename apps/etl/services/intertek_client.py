import json
import logging
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import requests
from django.core.cache import cache
from django.utils import timezone

from apps.etl import exceptions

logger = logging.getLogger(__name__)


class IntertekAPIClient:
    """
    Client for Intertek OILCM API operations.

    Manages authentication, token lifecycle, and file downloads from the
    Intertek inspection reporting system.

    Attributes:
        login_url: URL for authentication endpoint.
        api_base_url: Base URL for API endpoints.
        username: Username for authentication.
        password: Password for authentication.
        token_cache_key: Cache key for storing JWT token.
        token_expiry_cache_key: Cache key for storing token expiry time.
    """

    # API URLs
    LOGIN_URL = (
        "https://servicesintertek.sigcomt.com:2012/oilcm/api/Security/Login"
    )
    API_BASE_URL = "https://servicesintertek.sigcomt.com:2012/oilcm/api"
    REFERER_URL = "https://oilcmintertek.sigcomt.com:2015/"

    # Cache keys for token storage
    TOKEN_CACHE_KEY = "intertek_api_token"
    TOKEN_EXPIRY_CACHE_KEY = "intertek_api_token_expiry"

    # Token expiry buffer in seconds (renew 5 minutes before actual expiry)
    TOKEN_EXPIRY_BUFFER = 300

    def __init__(self, username: str, password: str) -> None:
        """
        Initialize the Intertek API client.

        Args:
            username: Username for API authentication.
            password: Password for API authentication.
        """
        self.username = username
        self.password = password
        self._session = requests.Session()
        self._setup_session_headers()

    def _setup_session_headers(self) -> None:
        """Configure default headers for all requests."""
        self._session.headers.update(
            {
                "Accept": "application/json, text/plain, */*",
                "Content-Type": "application/json",
                "Referer": self.REFERER_URL,
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/143.0.0.0 Safari/537.36"
                ),
            }
        )

    def _get_cached_token(self) -> Optional[str]:
        """
        Retrieve cached authentication token if valid.

        Returns:
            The cached token if available and not expired, None otherwise.
        """
        token = cache.get(self.TOKEN_CACHE_KEY)
        expiry = cache.get(self.TOKEN_EXPIRY_CACHE_KEY)

        if not token or not expiry:
            return None

        # Check if token is still valid (with buffer)
        if timezone.now() >= expiry - timedelta(
            seconds=self.TOKEN_EXPIRY_BUFFER
        ):
            logger.info("Cached token expired or about to expire")
            return None

        logger.debug("Using cached authentication token")
        return token

    def _cache_token(self, token: str, expires_in: int) -> None:
        """
        Cache authentication token with expiry time.

        Args:
            token: JWT token to cache.
            expires_in: Token lifetime in seconds.
        """
        expiry_time = timezone.now() + timedelta(seconds=expires_in)
        cache.set(self.TOKEN_CACHE_KEY, token, expires_in)
        cache.set(self.TOKEN_EXPIRY_CACHE_KEY, expiry_time, expires_in)
        logger.debug(f"Token cached until {expiry_time}")

    def _authenticate(self) -> str:
        """
        Authenticate with the Intertek API and obtain JWT token.

        Returns:
            JWT authentication token.

        Raises:
            AuthenticationError: If authentication fails.
        """
        logger.info(f"Authenticating user: {self.username}")

        payload = {
            "userName": self.username,
            "password": self.password,
            "rememberMe": False,
        }

        try:
            response = self._session.post(
                self.LOGIN_URL, json=payload, timeout=30
            )
            response.raise_for_status()

            data = response.json()

            if data.get("message"):
                error_msg = data.get("message", "Authentication failed")
                raise exceptions.AuthenticationError(
                    f"Login failed: {error_msg}"
                )

            token = data.get("data", {}).get("accessToken")
            if not token:
                raise exceptions.AuthenticationError(
                    "No token received from authentication"
                )

            # Calculate token expiry (typically 24 hours for this API)
            # Default to 24 hours if not specified
            expires_in = data.get("data", {}).get("expiresIn", 86400)
            self._cache_token(token, expires_in)

            logger.info("Authentication successful")
            return token

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication request failed: {e}")
            raise exceptions.AuthenticationError(
                f"Failed to authenticate: {str(e)}"
            ) from e
        except (KeyError, json.JSONDecodeError) as e:
            logger.error(f"Invalid authentication response: {e}")
            raise exceptions.AuthenticationError(
                f"Invalid response from authentication endpoint: {str(e)}"
            ) from e

    def get_token(self) -> str:
        """
        Get valid authentication token, refreshing if necessary.

        Returns:
            Valid JWT authentication token.

        Raises:
            AuthenticationError: If unable to obtain valid token.
        """
        # Try to get cached token first
        token = self._get_cached_token()
        if token:
            return token

        # Authenticate to get new token
        return self._authenticate()

    def _make_authenticated_request(
        self,
        method: str,
        url: str,
        **kwargs,
    ) -> requests.Response:
        """
        Make an authenticated API request with automatic token refresh.

        Args:
            method: HTTP method (GET, POST, etc.).
            url: Request URL.
            **kwargs: Additional arguments passed to requests.

        Returns:
            Response object.

        Raises:
            APIRequestError: If the request fails.
            TokenExpiredError: If token is expired and refresh fails.
        """
        token = self.get_token()

        # Add authorization header
        headers = kwargs.get("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        try:
            response = self._session.request(method, url, **kwargs)
            response.raise_for_status()
            return response

        except requests.exceptions.HTTPError as e:
            # Check if it's a 401 Unauthorized (token expired)
            if e.response.status_code == 401:
                logger.warning("Token expired, attempting to refresh")
                # Clear cache and try once more with fresh token
                cache.delete(self.TOKEN_CACHE_KEY)
                cache.delete(self.TOKEN_EXPIRY_CACHE_KEY)

                token = self.get_token()
                kwargs["headers"]["Authorization"] = f"Bearer {token}"

                try:
                    response = self._session.request(method, url, **kwargs)
                    response.raise_for_status()
                    return response
                except requests.exceptions.RequestException as retry_error:
                    raise exceptions.TokenExpiredError(
                        f"Token refresh failed: {str(retry_error)}"
                    ) from retry_error

            raise exceptions.APIRequestError(
                f"API request failed: {str(e)}"
            ) from e

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            raise exceptions.APIRequestError(f"Request failed: {str(e)}") from e

    def download_inspection_report(
        self,
        search_text: str = "",
        lab_number: str = "",
        page_number: int = 0,
        page_size: int = 50,
        sort_field: str = "Id",
        sort_type: int = 1,
        file_type: int = 3,
    ) -> Path:
        """
        Download inspection detail export file.

        Args:
            search_text: Text to search for in reports.
            lab_number: Laboratory number to filter by.
            page_number: Page number for pagination.
            page_size: Number of records per page.
            sort_field: Field to sort by.
            sort_type: Sort direction (1 for ascending, 0 for descending).
            file_type: Export file type (3 for Excel).

        Returns:
            Path to the downloaded file in temporary storage.

        Raises:
            FileDownloadError: If file download fails.
        """
        logger.info("Downloading inspection detail report")

        url = f"{self.API_BASE_URL}/Report/InspectionDetailExport"

        params = {
            "searchText": search_text,
            "labNumber": lab_number,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sortField": sort_field,
            "sortType": sort_type,
            "download": "true",
            "fileType": file_type,
        }

        try:
            response = self._make_authenticated_request(
                "GET", url, params=params, timeout=60
            )

            # Determine file extension based on file_type
            file_extensions = {
                1: ".csv",
                2: ".pdf",
                3: ".xlsx",
            }
            extension = file_extensions.get(file_type, ".xlsx")

            # Create temporary file with appropriate extension
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f"_intertek_report_{timestamp}{extension}",
                prefix="etl_",
            )

            # Write content to file
            temp_file.write(response.content)
            temp_file.close()

            file_path = Path(temp_file.name)
            logger.info(f"Report downloaded successfully to: {file_path}")

            return file_path

        except exceptions.APIRequestError as e:
            logger.error(f"Failed to download report: {e}")
            raise exceptions.FileDownloadError(
                f"Report download failed: {str(e)}"
            ) from e
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            raise exceptions.FileDownloadError(
                f"Unexpected error: {str(e)}"
            ) from e

    def get_inspection_details(
        self,
        search_text: str = "",
        lab_number: str = "",
        page_number: int = 0,
        page_size: int = 50,
        sort_field: str = "Id",
        sort_type: int = 1,
    ) -> Dict:
        """
        Get inspection details as JSON data.

        Args:
            search_text: Text to search for in reports.
            lab_number: Laboratory number to filter by.
            page_number: Page number for pagination.
            page_size: Number of records per page.
            sort_field: Field to sort by.
            sort_type: Sort direction (1 for ascending, 0 for descending).

        Returns:
            Dictionary containing inspection details.

        Raises:
            APIRequestError: If the request fails.
        """
        logger.info("Fetching inspection details")

        url = f"{self.API_BASE_URL}/Report/InspectionDetail"

        params = {
            "searchText": search_text,
            "labNumber": lab_number,
            "pageNumber": page_number,
            "pageSize": page_size,
            "sortField": sort_field,
            "sortType": sort_type,
        }

        try:
            response = self._make_authenticated_request(
                "GET", url, params=params, timeout=30
            )

            data = response.json()
            logger.info("Inspection details retrieved successfully")

            return data

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            raise exceptions.APIRequestError(
                f"Invalid response format: {str(e)}"
            ) from e

    def close(self) -> None:
        """Close the HTTP session and cleanup resources."""
        self._session.close()
        logger.debug("HTTP session closed")
