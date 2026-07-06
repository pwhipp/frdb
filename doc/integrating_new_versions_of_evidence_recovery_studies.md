# Integrating New Versions of Evidence Recovery Studies

This document defines the repeatable workflow for integrating a newly received
evidence recovery studies workbook into the maintained comparison workbook.

It applies to the current update using the source workbooks already archived in
`source_materials/`:

- `source_materials/interactive_evidence_recovery_comparison.xlsx`
- `source_materials/interactive_evidence_recovery_comparison_results.xlsx`

It is also intended to be reused for future incoming study-sheet updates.

## Goals

The integration must:

- preserve an unmodified source copy of each received workbook
- migrate the new studies sheet into the maintained comparison workbook
- update study rows, comparison rows, categories, scoring, filters, and summary
  outputs consistently
- make every manual judgment auditable
- avoid changing workbook mechanics silently
- leave a clear validation trail before final commit

The central distinction is that a study row is not necessarily a comparison row.
One new study may add zero, one, or many comparisons depending on the methods,
materials, substrates, workflows, equipment, and result dimensions reported by
that study.

## Data Roles

Each integration must identify these data roles before analysis starts.

### New Data Input

The new data input is the newly received studies workbook copied into
`source_materials/`.

For the current update, the new data input is:

```text
source_materials/interactive_evidence_recovery_comparison_results.xlsx
```

The new data input is read-only evidence. Use it to propose additions,
corrections, deletions, categorisation changes, and comparison-row changes. It
does not become canonical merely because it was received.

### Existing Canonical Workbook Data

The existing canonical workbook data is the last accepted maintained comparison
workbook before applying the new data input.

For the current update, the existing canonical workbook baseline is:

```text
source_materials/interactive_evidence_recovery_comparison.xlsx
```

This workbook supplies the existing studies sheet, existing comparison sheet,
current scoring mechanics, current workbook structure, and existing manual
curation decisions. Use it as the comparison baseline when deciding whether an
incoming study is new, duplicate, corrected, or out of scope.

The archived baseline must remain unchanged. If workbook editing is required,
create or use a working maintained workbook. After validation and commit, that
updated workbook becomes the new canonical workbook data for the next
integration.

### Generated Application Data

The generated application data is the JSON under `data/` produced from the
accepted canonical workbook by `script/analyze_workbook.py`.

Generated files include:

- `data/publications.json`
- `data/publication_filters.json`
- `data/filters.json`
- `data/filter_highlight_terms.json`
- `data/decision_map.json`
- `data/tables.json`

These files are outputs, not the input authority for study or comparison
decisions. Use existing generated data to preserve stable identifiers and to
compare before/after application behaviour. Regenerate it from the accepted
workbook instead of manually editing it.

## Updating Source Materials

`source_materials/` is the archive of received and baseline workbooks. It has
already been created, so future updates should add to it rather than recreate
it.

Before changing workbook content for any update:

1. Copy the newly received studies workbook into `source_materials/`.
2. Preserve the received file unchanged. If the incoming filename would
   overwrite an archived file, add an ISO date or received-version suffix to the
   copied filename.
3. Commit the copied source workbook before analysis or workbook editing.
4. Record the copied workbook as the new data input for the integration.
5. Record the last accepted maintained comparison workbook as the existing
   canonical workbook data.
6. Use the new data input to verify, add, and update the existing canonical
   studies and comparison data.
7. Do all migration and workbook editing in the maintained workbook or an
   explicit working copy, not in the archived source workbook.

For the current update, this baseline is recorded by commit:

```text
5b05d1e Add source workbook baselines
```

## Category Rules And Review Destination

Category changes must be explicit, reviewable, and then applied in the runtime
source of truth.

For each integration, create a category mapping audit before changing generated
data. The audit is the human-review destination for proposed category changes.
It may be a worksheet or CSV, but it must contain one row per distinct raw
biological-material value found in the maintained and incoming data.

The category mapping audit must include:

- raw biological-material value
- normalized match text
- proposed canonical category
- matching rule
- affected study rows
- affected comparison rows
- reviewer decision
- reviewer notes

After review, the accepted category rules must be applied in
`script/workbook_analysis/rule_definitions.py`. That file is the reviewable data
source of truth for application category generation. The functional code in
`script/workbook_analysis/rules.py` derives runtime mappings from those
definitions. Do not maintain a separate hidden workbook mapping, helper list, or
formula-based mapping that can diverge from it.

If a workbook sheet is useful for review, generate or copy it from the same
category mapping audit and label it as an audit artifact. It must not become a
second source of truth.

### Current Biological-Material Mapping

For the current update, apply this mapping:

| Raw value or normalized match | Canonical category | Notes |
| --- | --- | --- |
| `gdna`, including case and spacing variants such as `gDNA` | `Other` | Previously treated as a separate biological material. |
| `extracted dna` | `Other` | Include clear extracted-DNA synonyms only when the source value means extracted DNA. |
| `dna isolate` | `Other` | Treat as extracted DNA when used as the biological material. |
| `cfdna`, including `cfDNA` | `Other` | Previously treated as a separate biological material. |
| `human embryonic kidney cells` | `Other` | Include explicit HEK/HEK-cell wording only when it clearly refers to human embryonic kidney cells. |
| `buccal cells` | `Saliva` | Includes `buccal cell suspension`. |
| `buckle cells` | `Saliva` | Treat as a spelling variant of buccal cells. |

Normalize obvious spelling, case, punctuation, and spacing variants before
applying the mapping.

Use canonical display labels consistently. For the current application data,
that means `Other` and `Saliva`, not a mixture of differently cased labels.

## Integration Workflow

### 1. Inspect Workbook Structure

Record the structure of both workbooks before making changes:

- sheet names
- sheet dimensions
- header rows
- table ranges
- formulas
- named ranges
- validations
- filters
- merged ranges
- hidden rows or columns
- styling or colour semantics that affect interpretation

Identify:

- the new data input workbook
- the existing canonical workbook baseline
- the maintained studies sheet in the comparison workbook
- the incoming studies/results sheet in the new workbook
- the comparison sheet or sheets that derive one or more comparisons from each
  study
- any scoring or summary sheets that depend on the comparison data

### 2. Build a Study-Level Audit

Create a proposed study-level audit before editing the workbook.

Each study row from the new data input should be compared with the existing
canonical workbook data and classified as one of:

- new study
- existing study with unchanged data
- existing study with corrected or updated data
- duplicate row
- ambiguous match requiring human review
- out of scope

Match studies using stable bibliographic and content fields rather than row
position. Prefer title, authors, year, DOI, source link, method, material, and
study notes over spreadsheet order.

The audit should include:

- incoming row identifier
- matched maintained row identifier, if any
- proposed action
- reason for the proposed action
- fields that differ
- human decision
- reviewer notes

### 3. Expand Studies Into Comparisons

For every accepted new or updated study, determine the comparison rows it
creates or changes.

Use the workbook's existing comparison granularity. Do not assume one study
equals one comparison.

A study may need separate comparison rows for distinct:

- recovery methods
- equipment or techniques
- biological materials
- substrate types
- sample preparation conditions
- workflows
- datasets
- performance outcomes
- scoring-relevant result groups

Create a study-to-comparison audit with:

- maintained study identifier
- incoming study identifier
- proposed comparison identifier
- comparison dimensions
- category values after normalization
- scoring inputs
- proposed comparison action
- human decision
- reviewer notes

Flag the following for review:

- accepted studies that produce zero comparison rows
- studies that unexpectedly produce many comparison rows
- comparison rows with missing category values
- duplicated comparison keys
- comparison rows whose score cannot be derived from the available fields
- existing comparison rows that should be removed because the new source data
  supersedes them

### 4. Apply Category Normalisation

Apply category normalization to both new and existing affected records.

For the current update, specifically verify that:

- biological material categories no longer retain separate values for `gdna`,
  `extracted dna`, `cfdna`, or `human embryonic kidney cells` where they should
  roll up to `Other`
- buccal/buckle spelling variants roll up to `Saliva`
- filters, scoring sheets, and summaries use the normalized category values
- obsolete category labels are not left behind in helper ranges, lookup tables,
  validation lists, or cached summaries
- `script/workbook_analysis/rule_definitions.py` contains the accepted
  biological-material rules

### 5. Update the Maintained Workbook

After the audit decisions are settled:

1. Migrate accepted study rows from the new data input into the maintained
   workbook.
2. Update existing study rows where the incoming workbook corrects or supersedes
   existing canonical workbook data.
3. Add, update, or remove comparison rows according to the study-to-comparison
   audit.
4. Refresh formulas, table ranges, filters, helper columns, and validation
   lists.
5. Preserve formatting and workbook conventions unless a deliberate change is
   recorded.
6. Do not overwrite manual notes or scoring decisions without an audit entry.

### 6. Recalculate Scoring

Recalculate scores only after study and comparison rows have been fully
integrated.

Verify:

- every comparison row has all required scoring inputs
- missing or qualitative results are scored according to the existing scoring
  rules
- category changes are reflected in scoring groups
- score formulas cover the full expanded range
- summary totals and rankings update from the comparison data

Produce a score-change audit showing:

- comparison identifier
- previous score, if any
- new score
- changed scoring inputs
- reason for score change
- warnings or unresolved assumptions

Large or unexpected score changes require human review before finalising the
workbook.

## Human Verification Steps

The human reviewer should focus on domain judgment rather than mechanical
spreadsheet editing.

Required human review points:

1. Confirm which incoming study rows should be included, excluded, merged, or
   treated as duplicates.
2. Resolve ambiguous matches between incoming studies and maintained studies.
3. Confirm the number and meaning of comparison rows created by each accepted
   study.
4. Decide category edge cases that are not covered by the explicit category
   mapping audit.
5. Validate method, equipment, workflow, material, and substrate labels for each
   proposed comparison.
6. Confirm scoring assumptions for missing, qualitative, partial, or
   incomparable results.
7. Supply or correct missing metadata such as DOI, source link, citation,
   sample description, method names, and caveat notes.
8. Review the final integration summary before the workbook update is committed.

Useful review columns for audit sheets:

- `decision`
- `correct_category`
- `accepted_rule`
- `mapping_notes`
- `correct_comparison_count`
- `correct_method`
- `correct_material`
- `correct_score`
- `review_notes`

## Validation Checklist

Before committing the updated maintained workbook, verify:

- source workbooks remain unchanged in `source_materials/`
- the integration summary identifies the new data input and existing canonical
  workbook baseline
- all accepted new studies are present in the maintained studies sheet
- all accepted new comparisons are present in the comparison sheet
- every accepted study maps to the expected number of comparison rows
- no unintended duplicate studies exist
- no unintended duplicate comparison keys exist
- category rules have been applied consistently
- the accepted category mapping audit agrees with
  `script/workbook_analysis/rule_definitions.py`
- obsolete biological-material categories are absent from active filters and
  summaries
- formulas do not contain `#REF!`, `#VALUE!`, `#NAME?`, or other error values
- table ranges and filters include all new rows
- scoring formulas include all new comparison rows
- score changes are explained by source data, category changes, or accepted
  scoring decisions
- human review decisions have been applied
- unresolved warnings are documented

## Expected Outputs

Each integration should produce:

- data-role summary identifying the new data input, existing canonical workbook
  baseline, working workbook, and generated application outputs
- updated maintained comparison workbook
- study-level audit
- study-to-comparison audit
- category normalization summary
- category mapping audit
- score-change audit
- final validation summary
- commit or commits with clear messages

Suggested commit sequence:

1. Commit unchanged source workbooks.
2. Commit audited study and comparison migration.
3. Commit scoring, summary, and validation updates if they are substantial
   enough to deserve a separate review point.

## Current Update Execution Notes

For the current workbook update:

1. Use the committed source files in `source_materials/` as the baseline.
2. If a newer source workbook is received, copy it into `source_materials/` and
   commit it unchanged before analysis.
3. Treat `source_materials/interactive_evidence_recovery_comparison_results.xlsx`
   as the new data input.
4. Treat `source_materials/interactive_evidence_recovery_comparison.xlsx` as
   the existing canonical workbook baseline.
5. Do not change the sheets until the study-level, study-to-comparison, and
   category mapping audits have been prepared.
6. Pay particular attention to studies that introduce multiple comparisons.
7. Apply the biological-material category changes across both existing and new
   data.
8. Treat any scoring change caused by category rollups as expected only after it
   appears in the score-change audit.
