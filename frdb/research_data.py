from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path

from data.files import (
    FILTERS_JSON,
    FILTER_HIGHLIGHT_TERMS_JSON,
    PUBLICATIONS_JSON,
    data_dir,
)


DATA_DIR = data_dir(Path(__file__).resolve().parent.parent)
PUBLICATIONS_PATH = DATA_DIR / PUBLICATIONS_JSON
FILTERS_PATH = DATA_DIR / FILTERS_JSON
FILTER_HIGHLIGHT_TERMS_PATH = DATA_DIR / FILTER_HIGHLIGHT_TERMS_JSON


@lru_cache(maxsize=1)
def load_research_data() -> dict:
    return {
        "rows": load_json(PUBLICATIONS_PATH),
        "filters": load_json(FILTERS_PATH),
    }


@lru_cache(maxsize=1)
def load_filter_highlight_terms() -> dict:
    return load_json(FILTER_HIGHLIGHT_TERMS_PATH)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))
