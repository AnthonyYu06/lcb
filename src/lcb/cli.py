from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich import print

from .auth import create_gspread_client
from .config import GoogleSettings
from .sheets import pull_range, push_range, run_tests_from_sheet

app = typer.Typer(add_completion=False, help="CLI helper for Google Sheets workflows")


def load_settings(credentials: Optional[Path]) -> GoogleSettings:
    settings = GoogleSettings.from_env()
    if credentials:
        settings.service_account_file = credentials
    return settings


@app.command()
def configure(
    credentials: Path = typer.Option(
        None,
        "--credentials",
        file_okay=True,
        dir_okay=False,
        help="Path to a Google service account JSON file.",
    )
):
    """Validate that credentials are available and show the active scopes."""

    settings = load_settings(credentials)
    path = settings.require_credentials_path()
    print(f"Using credentials at [bold]{path}[/bold]")
    print("Scopes:")
    for scope in settings.scopes:
        print(f"- {scope}")


@app.command()
def pull(
    spreadsheet_id: str = typer.Argument(..., help="Spreadsheet ID from the URL"),
    range_a1: str = typer.Argument(..., help="Target range (A1 notation)"),
    worksheet: Optional[str] = typer.Option(
        None, "--worksheet", "-w", help="Worksheet title (defaults to the first sheet)"
    ),
    no_copy: bool = typer.Option(
        False, "--no-copy", help="Disable copying the pulled values to the clipboard"
    ),
    credentials: Path = typer.Option(
        None,
        "--credentials",
        file_okay=True,
        dir_okay=False,
        help="Path to a Google service account JSON file.",
    ),
):
    """Fetch a range and optionally place the values onto the clipboard."""

    settings = load_settings(credentials)
    client = create_gspread_client(settings)
    pull_range(
        client=client,
        spreadsheet_id=spreadsheet_id,
        range_a1=range_a1,
        worksheet_name=worksheet,
        copy=not no_copy,
    )


@app.command()
def push(
    spreadsheet_id: str = typer.Argument(..., help="Spreadsheet ID from the URL"),
    range_a1: str = typer.Argument(..., help="Target range (A1 notation)"),
    worksheet: Optional[str] = typer.Option(
        None, "--worksheet", "-w", help="Worksheet title (defaults to the first sheet)"
    ),
    stdin_text: bool = typer.Option(
        False,
        "--stdin",
        help="Read values from STDIN instead of the clipboard (tab-separated)",
    ),
    credentials: Path = typer.Option(
        None,
        "--credentials",
        file_okay=True,
        dir_okay=False,
        help="Path to a Google service account JSON file.",
    ),
):
    """Update a range using clipboard (or stdin) values."""

    settings = load_settings(credentials)
    client = create_gspread_client(settings)
    payload = sys.stdin.read() if stdin_text else None
    push_range(
        client=client,
        spreadsheet_id=spreadsheet_id,
        range_a1=range_a1,
        worksheet_name=worksheet,
        text=payload,
    )


@app.command()
def eval_tests(
    spreadsheet_id: str = typer.Argument(..., help="Spreadsheet ID from the URL"),
    worksheet: Optional[str] = typer.Option(
        None, "--worksheet", "-w", help="Worksheet title (defaults to the first sheet)"
    ),
    start_row: int = typer.Option(1, "--start-row", help="Row to begin reading tests"),
    expression_column: str = typer.Option(
        "A", "--expression-column", help="Column containing expressions to evaluate"
    ),
    expected_column: str = typer.Option(
        "B", "--expected-column", help="Column containing expected values"
    ),
    actual_column: str = typer.Option(
        "C", "--actual-column", help="Column to write the actual evaluation results"
    ),
    status_column: str = typer.Option(
        "D", "--status-column", help="Column to write PASS/FAIL/ERROR markers"
    ),
    credentials: Path = typer.Option(
        None,
        "--credentials",
        file_okay=True,
        dir_okay=False,
        help="Path to a Google service account JSON file.",
    ),
):
    """Run expressions in one column against expected values in another."""

    settings = load_settings(credentials)
    client = create_gspread_client(settings)
    run_tests_from_sheet(
        client=client,
        spreadsheet_id=spreadsheet_id,
        worksheet_name=worksheet,
        start_row=start_row,
        expression_column=expression_column,
        expected_column=expected_column,
        actual_column=actual_column,
        status_column=status_column,
    )


if __name__ == "__main__":  # pragma: no cover
    app()
