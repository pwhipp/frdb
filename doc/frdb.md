# FRDB

FRDB is a minimal web service providing users with 
- efficient filtering and sorting of, and subsequent clear presentation of the evidence recovery research data exemplified by /home/paul/wk/frdb/interactive_evidence_recovery_comparison_results.xls.

Presentation:
The table will be presented with the headings frozen so that it does not scroll off the top of the page and the first column (authors) frozen so that it does not scroll off the left of the page

The fields and their treatment are as follows:

Authors
    This field should appear as is and the link should be retained so that clicking on it will take the user to the research source.
No. of samples (replicates)
    This field is just reported as is for now.
Recovery Methods
    This field lists recovery methods investigated. These should be aggregated into a list of recovery methods that
    can be used for filtering (see below)
Equipment tested
    This field is a list of the equipment used to recover the evidence. The equipment should be aggregated into a list of equipment/techniques
Biological material
    This field is a list (often only one item) of the biological materials targeted for recovery
Substrate type
    A list of the substrate types (Porous or Non-porous) investigated
Statistical analysis
    Boolean field
STR analysis
    Boolean field
Results
    Summary text tield with rich formatting.
Key
    Result annotation? ignore for now
Instructions
    Not a colum really - ignore
Replicates column headers are really colour keys for the statistical analysis column background colours.

## Filtering

Users may filter the table using the following fields:
Recovery methods
Equipment tested
Biological material
Substrate type

For these fields we need the filter to offer the set of the relevant items and to allow the user to check one or more items (plus a select all/select none). Each filterable heading should show a drop down button which will be highlighted if there are items selected. Selecting the drop down button will present the list of items in a modal with a checkbox next to each.

Notes:

Use the latest bootstrap for presentation.

The table is to look familiar to users of excel or calc and the columns should be initialized at an appropriate width with the contents wrapping for results.

If templating is required, use jinja2.