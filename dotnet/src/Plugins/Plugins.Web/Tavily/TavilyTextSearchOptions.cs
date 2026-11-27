// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// Options used to construct an instance of <see cref="TavilyTextSearch"/>.
/// </summary>
public sealed class TavilyTextSearchOptions
{
    /// <summary>
    /// The URI endpoint of the Tavily search service. The URI must use HTTPS.
    /// </summary>
    public Uri? Endpoint { get; init; } = null;

    /// <summary>
    /// The depth of the search. advanced search is tailored to retrieve the
    /// most relevant sources and content snippets for your query,
    /// while basic search provides generic content snippets from each source.
    /// A basic search costs 1 API Credit, while an advanced search costs 2 API Credits.
    /// Available options: basic, advanced
    /// </summary>
    public TavilySearchDepth? SearchDepth { get; set; }

    /// <summary>
    /// The number of content chunks to retrieve from each source.
    /// Each chunk's length is maximum 500 characters.
    /// Available when search_depth is basic, advanced or fast.
    /// Required range: 1 - 3
    /// </summary>
    public int? ChunksPerSource { get; set; }

    /// <summary>
    /// Boost search results from a specific country, for example "united states".
    /// Available only when the search topic is general. Not supported with the <see cref="TavilySearchDepth.Fast"/>
    /// or <see cref="TavilySearchDepth.UltraFast"/> search depths, for which Tavily returns an error.
    /// </summary>
    public string? Country { get; set; }

    /// <summary>
    /// Return only results published or updated after this date (sent as YYYY-MM-DD).
    /// Not sent when null.
    /// </summary>
    public DateTime? StartDate { get; set; }

    /// <summary>
    /// Return only results published or updated before this date (sent as YYYY-MM-DD).
    /// Not sent when null.
    /// </summary>
    public DateTime? EndDate { get; set; }

    /// <summary>
    /// Whether to filter out adult or unsafe content from results.
    /// Not supported by Tavily for the fast or ultra-fast search depths. Not sent when null.
    /// </summary>
    public bool? SafeSearch { get; set; }

    /// <summary>
    /// Controls how the include domain filter is applied. Only sent when the search has at least
    /// one include domain, because Tavily rejects the mode without include domains. Not sent when null.
    /// </summary>
    public TavilyIncludeDomainsMode? IncludeDomainsMode { get; set; }

    /// <summary>
    /// Boost search results in a specific language. Accepts an ISO 639-1 code (for example "en" or "zh-cn")
    /// or an English language name (for example "english"). By default this only boosts matching-language
    /// results in ranking; set <see cref="FilterByLanguage"/> to strictly filter instead. Not sent when null.
    /// </summary>
    public string? Language { get; set; }

    /// <summary>
    /// Strictly filter out results that do not match <see cref="Language"/> instead of only boosting them.
    /// Tavily requires <see cref="Language"/> to be set and returns an error otherwise.
    /// Sent when not null, including an explicit false.
    /// </summary>
    public bool? FilterByLanguage { get; set; }

    /// <summary>
    /// Only return results containing the exact quoted phrase(s) in the query, bypassing synonyms or
    /// semantic variations. Wrap the target phrases in quotes within the query.
    /// Sent when not null, including an explicit false.
    /// </summary>
    public bool? ExactMatch { get; set; }

    /// <summary>
    /// Let Tavily configure search parameters automatically from the query's content and intent;
    /// explicitly set options still take precedence. <see cref="IncludeAnswer"/>, <see cref="IncludeRawContent"/>
    /// and the number of results are never set automatically. Tavily may raise the search depth to advanced,
    /// which uses 2 API credits per request; set <see cref="SearchDepth"/> to basic to avoid the extra cost.
    /// Sent when not null, including an explicit false.
    /// </summary>
    public bool? AutoParameters { get; set; }

    /// <summary>
    /// Include an LLM-generated answer to the provided query.
    /// basic or true returns a quick answer. advanced returns a more detailed answer.
    /// </summary>
    public bool? IncludeAnswer { get; set; }

    /// <summary>
    /// Include the cleaned and parsed HTML content of each search result.
    /// </summary>
    public bool? IncludeRawContent { get; set; }

    /// <summary>
    /// Also perform an image search and include the results in the response.
    /// </summary>
    public bool? IncludeImages { get; set; }

    /// <summary>
    /// When include_images is true, also add a descriptive text for each image.
    /// </summary>
    public bool? IncludeImageDescriptions { get; set; }

    /// <summary>
    /// The HTTP client to use for making requests.
    /// </summary>
    public HttpClient? HttpClient { get; init; } = null;

    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchStringMapper" /> instance that can map a <see cref="TavilySearchResult"/> to a <see cref="string"/>
    /// </summary>
    public ITextSearchStringMapper? StringMapper { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchResultMapper" /> instance that can map a <see cref="TavilySearchResult"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    public ITextSearchResultMapper? ResultMapper { get; init; } = null;
}
