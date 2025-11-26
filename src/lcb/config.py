from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

DEFAULT_SCOPES: Sequence[str] = (
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
)


@dataclass
class GoogleSettings:
    """Configuration for authenticating against Google APIs."""

    service_account_file: Path | None = None
    scopes: Iterable[str] = field(default_factory=lambda: DEFAULT_SCOPES)

    @classmethod
    def from_env(cls) -> "GoogleSettings":
        path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
        return cls(service_account_file=Path(path) if path else None)

    def require_credentials_path(self) -> Path:
        """Return a resolved credentials path or raise a helpful error."""

        if not self.service_account_file:
            raise ValueError(
                "Set GOOGLE_SERVICE_ACCOUNT_FILE to the path of your service account JSON file."
            )

        resolved = self.service_account_file.expanduser().resolve()
        if not resolved.exists():
            raise FileNotFoundError(
                f"Credentials file not found at {resolved}. Ensure the path is correct."
            )
        return resolved
