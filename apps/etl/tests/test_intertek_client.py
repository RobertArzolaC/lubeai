"""
Tests for Intertek API Client Service.

Test cases for authentication, token management, and file download
operations with the Intertek OILCM API.
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from django.core.cache import cache
from django.test import TestCase
from django.utils import timezone

from apps.etl import exceptions
from apps.etl.services import IntertekAPIClient


class IntertekAPIClientTestCase(TestCase):
    """Test cases for IntertekAPIClient service."""

    def setUp(self) -> None:
        """Set up test fixtures."""
        self.username = "testuser"
        self.password = "testpass"
        self.client = IntertekAPIClient(
            username=self.username, password=self.password
        )
        # Clear cache before each test
        cache.clear()

    def tearDown(self) -> None:
        """Clean up after tests."""
        self.client.close()
        cache.clear()

    def test_client_initialization(self) -> None:
        """Test that client initializes correctly with credentials."""
        self.assertEqual(self.client.username, self.username)
        self.assertEqual(self.client.password, self.password)
        self.assertIsNotNone(self.client._session)

    def test_session_headers_setup(self) -> None:
        """Test that default session headers are configured correctly."""
        headers = self.client._session.headers
        self.assertEqual(headers["Accept"], "application/json, text/plain, */*")
        self.assertEqual(headers["Content-Type"], "application/json")
        self.assertIn("User-Agent", headers)
        self.assertIn("Referer", headers)

    @patch("apps.etl.services.intertek_client.requests.Session.post")
    def test_authenticate_success(self, mock_post: Mock) -> None:
        """Test successful authentication returns token."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": True,
            "data": {"token": "test_token_123", "expiresIn": 86400},
        }
        mock_post.return_value = mock_response

        token = self.client._authenticate()

        self.assertEqual(token, "test_token_123")
        mock_post.assert_called_once()

        # Verify credentials were sent
        call_kwargs = mock_post.call_args[1]
        payload = call_kwargs["json"]
        self.assertEqual(payload["userName"], self.username)
        self.assertEqual(payload["password"], self.password)

    @patch("apps.etl.services.intertek_client.requests.Session.post")
    def test_authenticate_failure_no_success(self, mock_post: Mock) -> None:
        """Test authentication failure when success is False."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "success": False,
            "message": "Invalid credentials",
        }
        mock_post.return_value = mock_response

        with self.assertRaises(exceptions.AuthenticationError) as context:
            self.client._authenticate()

        self.assertIn("Invalid credentials", str(context.exception))

    @patch("apps.etl.services.intertek_client.requests.Session.post")
    def test_authenticate_failure_no_token(self, mock_post: Mock) -> None:
        """Test authentication failure when no token is returned."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True, "data": {}}
        mock_post.return_value = mock_response

        with self.assertRaises(exceptions.AuthenticationError) as context:
            self.client._authenticate()

        self.assertIn("No token received", str(context.exception))

    @patch("apps.etl.services.intertek_client.requests.Session.post")
    def test_authenticate_request_exception(self, mock_post: Mock) -> None:
        """Test authentication handles request exceptions."""
        import requests

        mock_post.side_effect = requests.exceptions.RequestException("Network error")

        with self.assertRaises(exceptions.AuthenticationError) as context:
            self.client._authenticate()

        self.assertIn("Failed to authenticate", str(context.exception))

    def test_cache_token(self) -> None:
        """Test that token is cached correctly with expiry time."""
        token = "test_token_123"
        expires_in = 3600

        self.client._cache_token(token, expires_in)

        cached_token = cache.get(IntertekAPIClient.TOKEN_CACHE_KEY)
        cached_expiry = cache.get(IntertekAPIClient.TOKEN_EXPIRY_CACHE_KEY)

        self.assertEqual(cached_token, token)
        self.assertIsNotNone(cached_expiry)
        self.assertTrue(cached_expiry > timezone.now())

    def test_get_cached_token_valid(self) -> None:
        """Test retrieval of valid cached token."""
        token = "cached_token_123"
        expiry_time = timezone.now() + timedelta(hours=1)

        cache.set(IntertekAPIClient.TOKEN_CACHE_KEY, token, 3600)
        cache.set(IntertekAPIClient.TOKEN_EXPIRY_CACHE_KEY, expiry_time, 3600)

        cached_token = self.client._get_cached_token()
        self.assertEqual(cached_token, token)

    def test_get_cached_token_expired(self) -> None:
        """Test that expired cached token returns None."""
        token = "expired_token"
        expiry_time = timezone.now() - timedelta(hours=1)

        cache.set(IntertekAPIClient.TOKEN_CACHE_KEY, token, 3600)
        cache.set(IntertekAPIClient.TOKEN_EXPIRY_CACHE_KEY, expiry_time, 3600)

        cached_token = self.client._get_cached_token()
        self.assertIsNone(cached_token)

    def test_get_cached_token_none(self) -> None:
        """Test that None is returned when no token is cached."""
        cached_token = self.client._get_cached_token()
        self.assertIsNone(cached_token)

    @patch.object(IntertekAPIClient, "_authenticate")
    @patch.object(IntertekAPIClient, "_get_cached_token")
    def test_get_token_uses_cache(
        self, mock_get_cached: Mock, mock_authenticate: Mock
    ) -> None:
        """Test that get_token uses cached token when available."""
        mock_get_cached.return_value = "cached_token"

        token = self.client.get_token()

        self.assertEqual(token, "cached_token")
        mock_get_cached.assert_called_once()
        mock_authenticate.assert_not_called()

    @patch.object(IntertekAPIClient, "_authenticate")
    @patch.object(IntertekAPIClient, "_get_cached_token")
    def test_get_token_authenticates_when_no_cache(
        self, mock_get_cached: Mock, mock_authenticate: Mock
    ) -> None:
        """Test that get_token authenticates when no cached token."""
        mock_get_cached.return_value = None
        mock_authenticate.return_value = "new_token"

        token = self.client.get_token()

        self.assertEqual(token, "new_token")
        mock_get_cached.assert_called_once()
        mock_authenticate.assert_called_once()

    @patch.object(IntertekAPIClient, "get_token")
    @patch("apps.etl.services.intertek_client.requests.Session.request")
    def test_make_authenticated_request_success(
        self, mock_request: Mock, mock_get_token: Mock
    ) -> None:
        """Test successful authenticated request."""
        mock_get_token.return_value = "valid_token"
        mock_response = Mock()
        mock_response.status_code = 200
        mock_request.return_value = mock_response

        response = self.client._make_authenticated_request(
            "GET", "https://example.com/api"
        )

        self.assertEqual(response, mock_response)
        mock_request.assert_called_once()

        # Verify authorization header
        call_kwargs = mock_request.call_args[1]
        self.assertEqual(
            call_kwargs["headers"]["Authorization"], "Bearer valid_token"
        )

    @patch.object(IntertekAPIClient, "get_token")
    @patch("apps.etl.services.intertek_client.requests.Session.request")
    def test_make_authenticated_request_token_expired_retry(
        self, mock_request: Mock, mock_get_token: Mock
    ) -> None:
        """Test that 401 error triggers token refresh and retry."""
        import requests

        # Create 401 response
        mock_response_401 = Mock()
        mock_response_401.status_code = 401

        # Create HTTPError with 401 response
        http_error = requests.exceptions.HTTPError("401 Unauthorized")
        http_error.response = mock_response_401

        # Create successful response
        mock_response_200 = Mock()
        mock_response_200.status_code = 200
        mock_response_200.raise_for_status.return_value = None

        mock_request.side_effect = [http_error, mock_response_200]
        mock_get_token.side_effect = ["expired_token", "new_token"]

        response = self.client._make_authenticated_request(
            "GET", "https://example.com/api"
        )

        self.assertEqual(response, mock_response_200)
        self.assertEqual(mock_get_token.call_count, 2)
        self.assertEqual(mock_request.call_count, 2)

    @patch.object(IntertekAPIClient, "get_token")
    @patch("apps.etl.services.intertek_client.requests.Session.request")
    def test_make_authenticated_request_api_error(
        self, mock_request: Mock, mock_get_token: Mock
    ) -> None:
        """Test that API errors are handled correctly."""
        import requests

        mock_get_token.return_value = "valid_token"
        mock_response = Mock()
        mock_response.status_code = 500

        http_error = requests.exceptions.HTTPError("Server Error")
        http_error.response = mock_response

        mock_request.side_effect = http_error

        with self.assertRaises(exceptions.APIRequestError):
            self.client._make_authenticated_request(
                "GET", "https://example.com/api"
            )

    @patch.object(IntertekAPIClient, "_make_authenticated_request")
    @patch("builtins.open", create=True)
    def test_download_inspection_report_success(
        self, mock_open: Mock, mock_request: Mock
    ) -> None:
        """Test successful report download."""
        mock_response = Mock()
        mock_response.content = b"Excel file content"
        mock_request.return_value = mock_response

        file_path = self.client.download_inspection_report()

        self.assertIsInstance(file_path, Path)
        self.assertTrue(str(file_path).endswith(".xlsx"))
        mock_request.assert_called_once()

        # Verify request parameters
        call_args = mock_request.call_args
        self.assertEqual(call_args[0][0], "GET")
        self.assertIn("InspectionDetailExport", call_args[0][1])

    @patch.object(IntertekAPIClient, "_make_authenticated_request")
    def test_download_inspection_report_failure(
        self, mock_request: Mock
    ) -> None:
        """Test report download handles errors."""
        mock_request.side_effect = exceptions.APIRequestError("Download failed")

        with self.assertRaises(exceptions.FileDownloadError) as context:
            self.client.download_inspection_report()

        self.assertIn("Report download failed", str(context.exception))

    @patch.object(IntertekAPIClient, "_make_authenticated_request")
    def test_download_inspection_report_custom_parameters(
        self, mock_request: Mock
    ) -> None:
        """Test report download with custom parameters."""
        mock_response = Mock()
        mock_response.content = b"Excel file content"
        mock_request.return_value = mock_response

        file_path = self.client.download_inspection_report(
            search_text="test",
            lab_number="LAB123",
            page_size=100,
            file_type=1,  # CSV
        )

        # Verify parameters were passed
        call_args = mock_request.call_args
        params = call_args[1]["params"]
        self.assertEqual(params["searchText"], "test")
        self.assertEqual(params["labNumber"], "LAB123")
        self.assertEqual(params["pageSize"], 100)
        self.assertEqual(params["fileType"], 1)

        # Verify file extension matches file type
        self.assertTrue(str(file_path).endswith(".csv"))

    @patch.object(IntertekAPIClient, "_make_authenticated_request")
    def test_get_inspection_details_success(
        self, mock_request: Mock
    ) -> None:
        """Test successful retrieval of inspection details."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "success": True,
            "data": [{"id": 1, "labNumber": "LAB123"}],
        }
        mock_request.return_value = mock_response

        result = self.client.get_inspection_details()

        self.assertTrue(result["success"])
        self.assertIn("data", result)
        mock_request.assert_called_once()

    @patch.object(IntertekAPIClient, "_make_authenticated_request")
    def test_get_inspection_details_invalid_json(
        self, mock_request: Mock
    ) -> None:
        """Test handling of invalid JSON response."""
        mock_response = Mock()
        mock_response.json.side_effect = json.JSONDecodeError(
            "Invalid JSON", "", 0
        )
        mock_request.return_value = mock_response

        with self.assertRaises(exceptions.APIRequestError) as context:
            self.client.get_inspection_details()

        self.assertIn("Invalid response format", str(context.exception))

    def test_close_session(self) -> None:
        """Test that close method closes the HTTP session."""
        with patch.object(self.client._session, "close") as mock_close:
            self.client.close()
            mock_close.assert_called_once()
