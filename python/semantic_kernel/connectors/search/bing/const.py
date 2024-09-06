# Copyright (c) Microsoft. All rights reserved.

from typing import Final

DEFAULT_URL: Final[str] = "https://api.bing.microsoft.com/v7.0/search"
DEFAULT_CUSTOM_URL: Final[str] = "https://api.bing.microsoft.com/"
QUERY_PARAMETERS: Final[list[str]] = [
    "answerCount",
    "cc",
    "freshness",
    "mkt",
    "promote",
    "responseFilter",
    "safeSearch",
    "setLang",
    "textDecorations",
    "textFormat",
]
QUERY_ADVANCED_SEARCH_KEYWORDS: Final[list[str]] = [
    "site",
    "contains",
    "ext",
    "filetype",
    "inanchor",
    "inbody",
    "intitle",
    "ip",
    "language",
    "loc",
    "location",
    "prefer",
    "feed",
    "hasfeed",
    "url",
]
