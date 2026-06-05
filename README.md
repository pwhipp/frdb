# Forensic Research Database (FRDB)

The goal of this database is to present users with published forensic recovery method research in a form that can be used to 
- determine the best recovery method given a particular substrate and biological fluid
- identify gaps or ommissions in the existing research

## Development notes

### Updating the research data

Research data is generated from an Excel workbook. Do not edit generated files in `data/` by hand.

To regenerate the main data module from a workbook:

```bash
.venv/bin/python script/analyze_workbook.py path/to/workbook.xlsx --output data/interactive_evidence_recovery_comparison_results.py
```

If `--output` is omitted, the script writes to `data/<workbook-name>.py`. The app imports every non-private module in `data/`, so use `--output` when replacing the existing dataset rather than adding a new one.

After updating data, run the Python verification commands:

```bash
.venv/bin/python -m compileall app.py frdb script data
.venv/bin/python - <<'PY'
from app import app
client = app.test_client()
index = client.get('/')
api = client.get('/api/research-data')
assert index.status_code == 200, index.status_code
assert api.status_code == 200, api.status_code
payload = api.get_json()
assert payload and payload.get('rows'), 'API returned no rows'
assert payload.get('filters'), 'API returned no filters'
PY
```

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
