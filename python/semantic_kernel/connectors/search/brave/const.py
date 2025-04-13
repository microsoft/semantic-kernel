# Copyright (c) Microsoft. All rights reserved.

from typing import Final

DEFAULT_URL: Final[str] = "https://api.search.brave.com/res/v1/web/search"
QUERY_PARAMETERS: Final[list[str]] = [
    "country",
    "search_lang",
    "ui_lang",
    "safesearch",
    "text_decorations",
    "spellcheck",
    "result_filter",
    "units",
]
