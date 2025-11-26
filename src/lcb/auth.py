from __future__ import annotations

import gspread
from google.oauth2.service_account import Credentials

from .config import GoogleSettings


def create_gspread_client(settings: GoogleSettings | None = None) -> gspread.Client:
    """Create an authenticated gspread client using service account credentials."""

    settings = settings or GoogleSettings.from_env()
    credentials_file = settings.require_credentials_path()
    credentials = Credentials.from_service_account_file(
        str(credentials_file), scopes=list(settings.scopes)
    )
    return gspread.authorize(credentials)
