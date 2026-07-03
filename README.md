# Forensic Research Database (FRDB)

The goal of this database is to present users with published forensic recovery method research in a form that can be used to:

- determine the best recovery method given a particular substrate and biological fluid
- identify gaps or omissions in the existing research

## Research Data Analysis

### Source workbook and generated data

Research JSON is generated from one reviewed workbook. Do not edit generated JSON files by hand.

- `interactive_evidence_recovery_comparison.xlsx` is the canonical source workbook.
- The first sheet, `studies`, contains the publication-level source rows used by the Publications table.
- The `Comparisons` sheet contains the reviewed structured comparison rows used by the decision map.

The old two-workbook flow with `recovery_comparisons.xlsx` is deprecated. Keep the reviewed comparisons in the same workbook as the studies so users can verify each comparison against the source study details without maintaining row-number references across files.

The `Comparisons.author` value is the study reference. Study authors in the `studies` sheet must be unique, and every comparison author must exactly match a study author.

Validate the workbook before generating data:

```bash
.venv/bin/python script/validate_workbook.py interactive_evidence_recovery_comparison.xlsx
```

The validator reports:

- duplicate study authors
- comparison sheet columns in the wrong order
- comparison rows whose `author` does not match a study
- studies with no comparison rows
- missing required comparison fields
- duplicate comparison rows

To regenerate the canonical data files after validation passes:

```bash
.venv/bin/python script/analyze_workbook.py interactive_evidence_recovery_comparison.xlsx
```

The script writes these files by default:

- `data/publications.json`: publication rows for the Publications table.
- `data/publication_filters.json`: per-publication filter values.
- `data/filters.json`: filter values for the Publications table API.
- `data/filter_highlight_terms.json`: terms used to highlight active publication filters.
- `data/decision_map.json`: home-page decision map, rankings, scoring README, and explanatory README content.
- `data/tables.json`: service table catalog and generated intermediate tables.

Use `--output-folder path/to/data` to write to a different folder. Use `--compact` to write compact JSON instead of the default indented JSON. Use `--comparisons-sheet SheetName` to validate or generate data from a non-canonical comparison sheet.

### `Comparisons` sheet

The expected `Comparisons` sheet columns are:

- `author`

Summary columns:

- `substrate_class`
- `biological_material_class`
- `better_method_class`
- `worse_method_class`
- `statistical_significance`

Detail columns:

- `substrate_detail`
- `biological_material_detail`
- `better_recovery_method`
- `worse_recovery_method`
- `comparison_scope`
- `notes_source_result_summary`

Use dropdowns for controlled classification fields where practical:

- `substrate_class`
- `biological_material_class`
- `better_method_class`
- `worse_method_class`
- `statistical_significance`

Do not use dropdowns for descriptive provenance fields such as `substrate_detail`, `biological_material_detail`, `better_recovery_method`, `worse_recovery_method`, `comparison_scope`, or `notes_source_result_summary`; those fields need source-specific wording.

Dropdowns are useful because method class and significance wording affects decision-map scoring. Keep the dropdown values aligned with the scoring rules before making the validator reject uncontrolled values. If a source result genuinely combines multiple method classes, prefer splitting it into separate comparison rows. If it cannot be split without overclaiming, use a clear combined value with ` / ` between controlled classes.

### Using AI to create initial comparisons

AI output is a draft extraction aid, not canonical data. Human review is required before using any AI-generated sheet for canonical data generation.

Create draft rows in a separate sheet such as `Comparisons_AI_Draft`, then compare them with the reviewed `Comparisons` sheet. Validate a draft sheet without replacing the canonical sheet:

```bash
.venv/bin/python script/validate_workbook.py interactive_evidence_recovery_comparison.xlsx --comparisons-sheet Comparisons_AI_Draft
```

Prompt for a full draft comparison sheet:

```text
Review each study in interactive_evidence_recovery_comparison.xlsx.
Use the studies sheet as the source evidence and create a draft comparison sheet named Comparisons_AI_Draft.
For each study, create one row for each recovery-method comparison supported by the source result summary.
Use the existing Comparisons columns exactly and in the same order.
The author value must exactly match the studies sheet author.
Classify substrate, biological material, recovery method classes, and statistical significance conservatively.
Preserve source-specific method and material wording in the detail fields.
Do not infer significance beyond the source result summary; if pairwise p-values are not stated, say so.
Do not delete or modify the reviewed Comparisons sheet.
```

Prompt for only studies that do not yet have comparisons:

```text
Review interactive_evidence_recovery_comparison.xlsx.
Compare the studies sheet with the existing Comparisons sheet by exact author value.
Create draft comparison rows only for studies whose author does not already appear in Comparisons.
Use the existing Comparisons columns exactly and in the same order, and write the draft rows to a new sheet named Comparisons_AI_Missing.
Do not modify existing comparison rows.
If every study already has at least one comparison, report that no draft rows are needed.
```

Validate a missing-only draft sheet with partial coverage allowed:

```bash
.venv/bin/python script/validate_workbook.py interactive_evidence_recovery_comparison.xlsx --comparisons-sheet Comparisons_AI_Missing --allow-missing-comparisons
```

After review, copy accepted draft rows into `Comparisons`, run the validator, then regenerate the canonical data.

## Development Notes

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
