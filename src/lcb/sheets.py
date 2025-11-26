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


def _column_to_index(column: str) -> int:
    column = column.strip().upper()
    if not column.isalpha():
        raise ValueError(f"Invalid column name: {column}")

    index = 0
    for char in column:
        index = index * 26 + (ord(char) - ord("A") + 1)
    return index


def _index_to_column(index: int) -> str:
    if index < 1:
        raise ValueError("Column index must be positive")

    letters: List[str] = []
    while index:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(remainder + ord("A")))
    return "".join(reversed(letters))


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
    expression_column: str = "A",
    expected_column: str = "B",
    actual_column: str = "C",
    status_column: str = "D",
) -> List[List[str]]:
    """Evaluate expressions in one column against expectations in another."""

    worksheet = resolve_worksheet(client, spreadsheet_id, worksheet_name)

    expression_idx = _column_to_index(expression_column)
    expected_idx = _column_to_index(expected_column)
    actual_col = _index_to_column(_column_to_index(actual_column))
    status_col = _index_to_column(_column_to_index(status_column))

    start_idx = min(expression_idx, expected_idx)
    end_idx = max(expression_idx, expected_idx)
    start_col = _index_to_column(start_idx)
    end_col = _index_to_column(end_idx)

    values = worksheet.get(f"{start_col}{start_row}:{end_col}")
    expr_offset = expression_idx - start_idx
    expected_offset = expected_idx - start_idx

    outputs: List[List[str]] = []
    for row in values:
        code = row[expr_offset].strip() if len(row) > expr_offset else ""
        expected = row[expected_offset].strip() if len(row) > expected_offset else ""

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
        actual_values = [[row[0]] for row in outputs]
        status_values = [[row[1]] for row in outputs]
        worksheet.update(
            f"{actual_col}{start_row}:{actual_col}{end_row}", actual_values
        )
        worksheet.update(
            f"{status_col}{start_row}:{status_col}{end_row}", status_values
        )
    console.print(f"Evaluated {len(outputs)} rows of expressions.")
    return outputs
