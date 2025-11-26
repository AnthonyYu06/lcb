from __future__ import annotations

import csv
import io
from typing import Iterable, List, Sequence

import pyperclip


def values_to_clipboard(values: Sequence[Sequence[str]]) -> str:
    """Copy a 2D sequence of strings to the clipboard as tab-separated values."""

    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter="\t")
    writer.writerows(values)
    text = buffer.getvalue().rstrip("\n")
    pyperclip.copy(text)
    return text


def clipboard_to_values(text: str | None = None) -> List[List[str]]:
    """Convert tab or comma separated clipboard text into a 2D list."""

    payload = text if text is not None else pyperclip.paste()
    rows: List[List[str]] = []
    for raw_line in payload.strip().splitlines():
        # Respect tab-separated values to preserve spacing from spreadsheets.
        delimiter = "\t" if "\t" in raw_line else ","
        rows.append([cell.strip() for cell in raw_line.split(delimiter)])
    return rows
