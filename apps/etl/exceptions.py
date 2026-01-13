"""
Custom exceptions for ETL operations.

This module defines exception classes for handling errors in ETL processes,
particularly for API authentication and data extraction operations.
"""


class ETLException(Exception):
    """Base exception for all ETL-related errors."""

    pass


class AuthenticationError(ETLException):
    """Raised when authentication with external API fails."""

    pass


class TokenExpiredError(ETLException):
    """Raised when the authentication token has expired."""

    pass


class APIRequestError(ETLException):
    """Raised when an API request fails."""

    pass


class FileDownloadError(ETLException):
    """Raised when file download fails."""

    pass
