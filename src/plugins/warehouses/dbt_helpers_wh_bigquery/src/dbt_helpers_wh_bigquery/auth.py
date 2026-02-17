"""Authentication utilities for BigQuery, including Service Account Impersonation."""

from typing import Any

from google.auth import default
from google.auth.impersonated_credentials import Credentials as ImpersonatedCredentials
from google.oauth2 import service_account

_BQ_SCOPES = ["https://www.googleapis.com/auth/cloud-platform"]
_DEFAULT_LIFETIME = 3600


def get_credentials(config: dict[str, Any]) -> Any:
    """Obtain credentials for BigQuery access.

    Supports:
    - Keyfile (service account JSON)
    - Application Default Credentials (ADC)
    - Service Account Impersonation (chained credentials)

    Args:
        config: Connection configuration. May include:
            - keyfile: Path to service account JSON keyfile
            - impersonate_service_account: Email of target SA to impersonate

    Returns:
        google.auth.Credentials suitable for BigQuery client.
    """
    creds: Any = None
    if config.get("keyfile"):
        creds = service_account.Credentials.from_service_account_file(
            config["keyfile"],
            scopes=_BQ_SCOPES,
        )
    else:
        creds, _ = default(scopes=_BQ_SCOPES)

    if config.get("impersonate_service_account"):
        creds = ImpersonatedCredentials(
            source_credentials=creds,
            target_principal=config["impersonate_service_account"],
            target_scopes=_BQ_SCOPES,
            lifetime=config.get("impersonation_lifetime", _DEFAULT_LIFETIME),
        )
    return creds
