# Copyright (c) Microsoft. All rights reserved.


from typing import Final

CUSTOM_SEARCH_URL: Final[str] = "https://www.googleapis.com/customsearch/v1"

# For more info on this list: https://developers.google.com/custom-search/v1/reference/rest/v1/cse/list
QUERY_PARAMETERS: Final[list[str]] = [
    # Country, Restricts search results to documents originating in a particular country.
    # You may use Boolean operators in the cr parameter's value.
    "cr",
    # Date Restrict, Restricts results to URLs based on date. Supported values include:
    # d[number]: requests results from the specified number of past days.
    # w[number]: requests results from the specified number of past weeks.
    # m[number]: requests results from the specified number of past months.
    # y[number]: requests results from the specified number of past years.
    "dateRestrict",
    # exactTerms, Identifies a phrase that all documents in the search results must contain.
    "exactTerms",
    # excludeTerms, Identifies a word or phrase that should not appear in any documents in the search results.
    "excludeTerms",
    # fileType, Restricts results to files of a specified extension. A list of file types indexable by Google
    # can be found in Search Console Help Center: https://support.google.com/webmasters/answer/35287
    "fileType",
    # filter, Controls turning on or off the duplicate content filter.
    "filter",
    # gl, Geolocation of end user. The gl parameter value is a two-letter country code. The gl parameter boosts search
    # results whose country of origin matches the parameter value.
    # See the Country Codes page for a list of valid values.
    "gl",
    # highRange, Specifies the ending value for a search range.
    "highRange",
    # hl, Sets the user interface language.
    "hl",
    # linkSite, Specifies that all search results should contain a link to a particular URL.
    "linkSite",
    # Language of the result. Restricts the search to documents written in a particular language (e.g., lr=lang_ja).
    "lr",
    # or Terms, Provides additional search terms to check for in a document, where each document in the search results
    # must contain at least one of the additional search terms.
    "orTerms",
    # rights, Filters based on licensing. Supported values include:
    # cc_publicdomain, cc_attribute, cc_sharealike, cc_noncommercial, cc_nonderived
    "rights",
    # siteSearch, Specifies all search results should be pages from a given site.
    "siteSearch",
    # siteSearchFilter, Controls whether to include or exclude results from the site named in the siteSearch parameter.
    "siteSearchFilter",
]
