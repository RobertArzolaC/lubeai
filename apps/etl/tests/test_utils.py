"""
Tests for ETL utility functions.

Test cases for helper functions that create and configure
API client instances.
"""

from unittest.mock import patch

from constance.test import override_config
from django.test import TestCase

from apps.etl import exceptions, utils
from apps.etl.services import IntertekAPIClient


class GetIntertekClientTestCase(TestCase):
    """Test cases for get_intertek_client utility function."""

    @override_config(
        INTERTEK_API_ENABLED=True,
        INTERTEK_API_USERNAME="testuser",
        INTERTEK_API_PASSWORD="testpass",
    )
    def test_get_client_with_valid_config(self) -> None:
        """Test that client is created with valid configuration."""
        client = utils.get_intertek_client()

        self.assertIsInstance(client, IntertekAPIClient)
        self.assertEqual(client.username, "testuser")
        self.assertEqual(client.password, "testpass")

    @override_config(INTERTEK_API_ENABLED=False)
    def test_get_client_when_disabled(self) -> None:
        """Test that exception is raised when API is disabled."""
        with self.assertRaises(exceptions.ETLException) as context:
            utils.get_intertek_client()

        self.assertIn("disabled", str(context.exception))

    @override_config(
        INTERTEK_API_ENABLED=True,
        INTERTEK_API_USERNAME="",
        INTERTEK_API_PASSWORD="testpass",
    )
    def test_get_client_with_missing_username(self) -> None:
        """Test that exception is raised when username is missing."""
        with self.assertRaises(exceptions.ETLException) as context:
            utils.get_intertek_client()

        self.assertIn("not configured", str(context.exception))

    @override_config(
        INTERTEK_API_ENABLED=True,
        INTERTEK_API_USERNAME="testuser",
        INTERTEK_API_PASSWORD="",
    )
    def test_get_client_with_missing_password(self) -> None:
        """Test that exception is raised when password is missing."""
        with self.assertRaises(exceptions.ETLException) as context:
            utils.get_intertek_client()

        self.assertIn("not configured", str(context.exception))
