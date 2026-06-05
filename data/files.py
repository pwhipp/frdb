from __future__ import annotations

from pathlib import Path


DATA_DIR_NAME = "data"
PUBLICATIONS_JSON = "publications.json"
PUBLICATION_FILTERS_JSON = "publication_filters.json"
FILTERS_JSON = "filters.json"
FILTER_HIGHLIGHT_TERMS_JSON = "filter_highlight_terms.json"


def data_dir(repo_root: Path) -> Path:
    return repo_root / DATA_DIR_NAME
