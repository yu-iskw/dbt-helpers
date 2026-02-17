"""Unit tests for BigQuery auth module."""

import unittest
from unittest.mock import MagicMock, patch

from dbt_helpers_wh_bigquery.auth import get_credentials


class TestGetCredentials(unittest.TestCase):
    """Tests for get_credentials."""

    @patch("dbt_helpers_wh_bigquery.auth.default")
    def test_uses_adc_when_no_keyfile(self, mock_default):
        """When no keyfile, uses Application Default Credentials."""
        mock_creds = MagicMock()
        mock_default.return_value = (mock_creds, "project-id")
        result = get_credentials({})
        mock_default.assert_called_once()
        self.assertIs(result, mock_creds)

    @patch("dbt_helpers_wh_bigquery.auth.service_account")
    def test_uses_keyfile_when_provided(self, mock_sa):
        """When keyfile provided, uses service account credentials."""
        mock_creds = MagicMock()
        mock_sa.Credentials.from_service_account_file.return_value = mock_creds
        result = get_credentials({"keyfile": "/path/to/key.json"})
        mock_sa.Credentials.from_service_account_file.assert_called_once()
        self.assertIs(result, mock_creds)

    @patch("dbt_helpers_wh_bigquery.auth.ImpersonatedCredentials")
    @patch("dbt_helpers_wh_bigquery.auth.default")
    def test_impersonation_when_configured(self, mock_default, mock_impersonated):
        """When impersonate_service_account set, chains credentials."""
        mock_base = MagicMock()
        mock_default.return_value = (mock_base, "project-id")
        mock_impersonated.return_value = MagicMock()
        get_credentials(
            {"impersonate_service_account": "target@project.iam.gserviceaccount.com"}
        )
        mock_impersonated.assert_called_once()
        call_kw = mock_impersonated.call_args[1]
        self.assertIs(call_kw["source_credentials"], mock_base)
        self.assertEqual(call_kw["target_principal"], "target@project.iam.gserviceaccount.com")
