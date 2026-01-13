"""
Tests for ETL exceptions.

Test cases for custom exception classes used in ETL operations.
"""

from django.test import TestCase

from apps.etl import exceptions


class ETLExceptionsTestCase(TestCase):
    """Test cases for ETL exception classes."""

    def test_etl_exception_base(self) -> None:
        """Test base ETLException can be raised and caught."""
        with self.assertRaises(exceptions.ETLException) as context:
            raise exceptions.ETLException("Base error")

        self.assertEqual(str(context.exception), "Base error")

    def test_authentication_error(self) -> None:
        """Test AuthenticationError is a subclass of ETLException."""
        self.assertTrue(
            issubclass(exceptions.AuthenticationError, exceptions.ETLException)
        )

        with self.assertRaises(exceptions.AuthenticationError) as context:
            raise exceptions.AuthenticationError("Auth failed")

        self.assertEqual(str(context.exception), "Auth failed")

    def test_token_expired_error(self) -> None:
        """Test TokenExpiredError is a subclass of ETLException."""
        self.assertTrue(
            issubclass(exceptions.TokenExpiredError, exceptions.ETLException)
        )

        with self.assertRaises(exceptions.TokenExpiredError) as context:
            raise exceptions.TokenExpiredError("Token expired")

        self.assertEqual(str(context.exception), "Token expired")

    def test_api_request_error(self) -> None:
        """Test APIRequestError is a subclass of ETLException."""
        self.assertTrue(
            issubclass(exceptions.APIRequestError, exceptions.ETLException)
        )

        with self.assertRaises(exceptions.APIRequestError) as context:
            raise exceptions.APIRequestError("Request failed")

        self.assertEqual(str(context.exception), "Request failed")

    def test_file_download_error(self) -> None:
        """Test FileDownloadError is a subclass of ETLException."""
        self.assertTrue(
            issubclass(exceptions.FileDownloadError, exceptions.ETLException)
        )

        with self.assertRaises(exceptions.FileDownloadError) as context:
            raise exceptions.FileDownloadError("Download failed")

        self.assertEqual(str(context.exception), "Download failed")

    def test_exception_inheritance_chain(self) -> None:
        """Test that all exceptions inherit from ETLException."""
        exception_classes = [
            exceptions.AuthenticationError,
            exceptions.TokenExpiredError,
            exceptions.APIRequestError,
            exceptions.FileDownloadError,
        ]

        for exc_class in exception_classes:
            with self.assertRaises(exceptions.ETLException):
                raise exc_class("Test error")
