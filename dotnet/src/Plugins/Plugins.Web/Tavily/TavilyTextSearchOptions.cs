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
    /// Available only when search_depth is advanced.
    /// Required range: 0 - 3
    /// </summary>
    public int? ChunksPerSource { get; set; }

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
