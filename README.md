# Forensic Research Database (FRDB)

The goal of this database is to present users with published forensic recovery method research in a form that can be used to:

- determine the best recovery method given a particular substrate and biological fluid
- identify gaps or omissions in the existing research

## Development notes

### Updating the research data

Research JSON is generated from two workbook sources. Do not edit generated JSON files by hand.

- `/home/paul/wk/frdb/interactive_evidence_recovery_comparison_results.xlsx` is the publication-level source workbook.
- `/home/paul/wk/frdb/recovery_comparisons.xlsx` is the curated comparison workbook used by the decision map.

The comparison workbook is needed because the publication workbook stores study outcomes as narrative text. The decision map requires structured, study-level comparison rows: substrate class, biological material class, better/worse recovery method, and statistical significance. Those fields require forensic interpretation and should be reviewed as curated data, not silently inferred during application startup.

To regenerate the canonical data files after both workbooks are current:

```bash
.venv/bin/python script/analyze_workbook.py /home/paul/wk/frdb/interactive_evidence_recovery_comparison_results.xlsx --comparisons-workbook /home/paul/wk/frdb/recovery_comparisons.xlsx
```

The script writes these files by default:

- `data/publications.json`: publication rows for the Publications table.
- `data/publication_filters.json`: per-publication filter values.
- `data/filters.json`: filter values for the Publications table API.
- `data/filter_highlight_terms.json`: terms used to highlight active publication filters.
- `data/decision_map.json`: home-page decision map, rankings, scoring README, and explanatory README content.
- `data/tables.json`: service table catalog and generated intermediate tables.

Use `--output-folder path/to/data` to write to a different folder. Use `--compact` to write compact JSON instead of the default indented JSON.

### Regenerating `recovery_comparisons.xlsx`

When the publication workbook changes, update `/home/paul/wk/frdb/recovery_comparisons.xlsx` before running `script/analyze_workbook.py`. Use Codex or another reviewed extraction workflow with this prompt:

```text
Review each study in ~/wk/frdb/interactive_evidence_recovery_comparison_results.xlsx. Classify the substrate as porous or non-porous. Classify the biological material using the FRDB material classes where possible: touch DNA, blood, saliva, buccal cells, gDNA, extracted DNA, cfDNA, semen, sweat, buffy coat, or various. Classify the equipment/recovery method as tape lift, moist swab, wet swab, wet-dry swab, swab with unspecified moisture, or other recovery method. For each study, for each recovery method comparison in the study list the author, substrate, biological material, better recovery method, worse recovery method, statistical significance. Generate a new spreadsheet containing this data ~/wk/frdb/recovery_comparisons.xlsx.
```

The expected `Comparisons` sheet columns are:

- `source_excel_row`
- `author`
- `substrate_class`
- `substrate_detail`
- `biological_material_class`
- `biological_material_detail`
- `better_recovery_method`
- `better_method_class`
- `worse_recovery_method`
- `worse_method_class`
- `statistical_significance`
- `comparison_scope`
- `notes_source_result_summary`

The data-generation script validates that every comparison row references a publication in the current source workbook and that `source_excel_row` values match the current workbook row numbers.

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
