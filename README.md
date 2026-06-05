# Forensic Research Database (FRDB)

The goal of this database is to present users with published forensic recovery method research in a form that can be used to 
- determine the best recovery method given a particular substrate and biological fluid
- identify gaps or ommissions in the existing research

## Development notes

### Updating the research data

Research JSON is generated from an Excel workbook into ignored files under `data/`. Do not edit generated JSON files by hand.

To regenerate the canonical data files from a workbook:

```bash
.venv/bin/python script/analyze_workbook.py path/to/workbook.xlsx
```

The script writes these files by default:

- `data/publications.json`: publication rows for the main table.
- `data/filters.json`: filter values for the table API.
- `data/filter_highlight_terms.json`: filter highlight terms embedded into the home page.

Use `--output-folder path/to/data` to write to a different folder. Use `--compact` to write compact JSON instead of the default indented JSON.

### Running a local test environment

Create the virtual environment and install runtime dependencies:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r deploy/requirements.txt
```

Create local settings if they are not already present:

```bash
cp local_settings.example.py local_settings.py
```

`local_settings.py` is ignored by Git. Update it with local contact, upload, and mail settings as needed. Pages and read-only data endpoints work with placeholder mail settings, but contact and proposal email flows require valid SMTP credentials.

Run the local Flask app:

```bash
.venv/bin/python app.py
```

Then open `http://127.0.0.1:5000/` and verify the data API at `http://127.0.0.1:5000/api/research-data`.
