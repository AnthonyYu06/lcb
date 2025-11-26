from __future__ import annotations

import math
from typing import Iterable, List, Sequence

import gspread
from gspread.exceptions import WorksheetNotFound
from rich.console import Console
from rich.table import Table

from .clipboard import clipboard_to_values, values_to_clipboard

console = Console()
SAFE_GLOBALS = {
    "__builtins__": {},
    "abs": abs,
    "min": min,
    "max": max,
    "sum": sum,
    "len": len,
    "round": round,
    "math": math,
}


def resolve_worksheet(
    client: gspread.Client, spreadsheet_id: str, worksheet_name: str | None
) -> gspread.Worksheet:
    spreadsheet = client.open_by_key(spreadsheet_id)
    if worksheet_name:
        try:
            return spreadsheet.worksheet(worksheet_name)
        except WorksheetNotFound:
            raise WorksheetNotFound(
                f"Worksheet '{worksheet_name}' not found in spreadsheet {spreadsheet_id}"
            )
    return spreadsheet.sheet1


def render_table(values: Sequence[Sequence[str]]) -> None:
    if not values:
        console.print("[yellow]No data returned[/yellow]")
        return

    table = Table(show_lines=False)
    # Header row if present, otherwise auto width.
    first_row = values[0]
    for index, cell in enumerate(first_row):
        header = cell or f"Column {index + 1}"
        table.add_column(header, overflow="fold")

    for row in values:
        table.add_row(*row)

    console.print(table)


def pull_range(
    client: gspread.Client,
    spreadsheet_id: str,
    range_a1: str,
    worksheet_name: str | None = None,
    copy: bool = True,
) -> Sequence[Sequence[str]]:
    worksheet = resolve_worksheet(client, spreadsheet_id, worksheet_name)
    values = worksheet.get(range_a1)
    if copy:
        values_to_clipboard(values)
        console.print(f"Copied {len(values)} rows to clipboard.")
    render_table(values)
    return values


def push_range(
    client: gspread.Client,
    spreadsheet_id: str,
    range_a1: str,
    worksheet_name: str | None = None,
    text: str | None = None,
) -> List[List[str]]:
    worksheet = resolve_worksheet(client, spreadsheet_id, worksheet_name)
    values = clipboard_to_values(text=text)
    if not values:
        raise ValueError("Clipboard is empty or not formatted as rows.")
    worksheet.update(range_a1, values)
    console.print(f"Updated range {range_a1} with {len(values)} rows.")
    return values


def evaluate_expression(expression: str) -> str:
    """Evaluate a Python expression with limited globals and return a string result."""

    compiled = compile(expression, "<sheet-expression>", "eval")
    result = eval(compiled, SAFE_GLOBALS, {})
    return str(result)


def run_tests_from_sheet(
    client: gspread.Client,
    spreadsheet_id: str,
    worksheet_name: str | None = None,
    start_row: int = 1,
) -> List[List[str]]:
    """Evaluate expressions in column A against expected values in column B."""

    worksheet = resolve_worksheet(client, spreadsheet_id, worksheet_name)
    values = worksheet.get(f"A{start_row}:B")

    outputs: List[List[str]] = []
    for row in values:
        code = row[0].strip() if row and len(row) > 0 else ""
        expected = row[1].strip() if len(row) > 1 else ""

        if not code:
            outputs.append(["", "NO CODE"])
            continue

        try:
            actual = evaluate_expression(code)
            status = "PASS" if expected and actual == expected else "FAIL"
            if not expected:
                status = "NO EXPECTATION"
        except Exception as exc:  # pragma: no cover - surfaced to the sheet
            actual = f"Error: {exc}"
            status = "ERROR"

        outputs.append([actual, status])

    if outputs:
        end_row = start_row + len(outputs) - 1
        worksheet.update(f"C{start_row}:D{end_row}", outputs)
    console.print(f"Evaluated {len(outputs)} rows of expressions.")
    return outputs
