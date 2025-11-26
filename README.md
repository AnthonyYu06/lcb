# lcb

Local clipboard helper for Google Sheets workflows.

This tool is designed for quick copy/paste workflows between your desktop clipboard and specific ranges in Google Sheets. It uses a Google service account to authenticate and provides a minimal CLI you can wire into global hotkeys or shell scripts.

## Setup

1. Create a Google Cloud service account with access to the target spreadsheet.
2. Download the service account JSON file and set an environment variable pointing to it:

   ```bash
   export GOOGLE_SERVICE_ACCOUNT_FILE=/path/to/service-account.json
   ```
3. Install the package locally (editable mode recommended while iterating):

   ```bash
   python -m pip install -e .
   ```

## Usage

The CLI is available via the `lcb` entry point.

### Validate credentials

```bash
lcb configure --credentials /path/to/service-account.json
```

### Copy a range to your clipboard

```bash
lcb pull <spreadsheet-id> "Sheet1!A1:C10"
```

Values are printed to the terminal and copied to your clipboard as tab-separated rows.

### Paste clipboard into a range

Copy rows (tab-separated) into your clipboard and run:

```bash
lcb push <spreadsheet-id> "Sheet1!A1:C10"
```

To supply data via stdin instead of the clipboard:

```bash
echo -e "a\tb\tc" | lcb push <spreadsheet-id> "Sheet1!A1:C1" --stdin
```

### Evaluate sheet-based tests

Place Python expressions in column A and expected values in column B. Then run:

```bash
lcb eval-tests <spreadsheet-id> --worksheet Sheet1 --start-row 1
```

Results are written back to columns C (actual value) and D (PASS/FAIL/ERROR).

## Notes

- The first worksheet is used by default; target a specific sheet via `--worksheet`.
- Scopes include spreadsheet access and drive file access so the service account can open files shared with it.
- Errors surface directly (e.g., missing worksheet or credentials) so you can adjust your workflow quickly.
