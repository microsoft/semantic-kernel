// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Options used to construct an instance of <see cref="BingTextSearch"/>
/// </summary>
public sealed class BingTextSearchOptions
{
    /// <summary>
    /// The URI endpoint of the Bing search service. The URI must use HTTPS.
    /// </summary>
    public Uri? Endpoint { get; init; } = null;

    /// <summary>
    /// The HTTP client to use for making requests.
    /// </summary>
    public HttpClient? HttpClient { get; init; } = null;

    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchStringMapper" /> instance that can map a <see cref="BingWebPage"/> to a <see cref="string"/>
    /// </summary>
    public ITextSearchStringMapper? StringMapper { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchResultMapper" /> instance that can map a <see cref="BingWebPage"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    public ITextSearchResultMapper? ResultMapper { get; init; } = null;

    /// <summary>
    /// Gets or sets the market where results come from (e.g., "en-US").
    /// Applied as a default to every search from this instance.
    /// See <see href="https://learn.microsoft.com/en-us/bing/search-apis/bing-web-search/reference/market-codes"/>.
    /// </summary>
    public string? Market { get; init; }

    /// <summary>
    /// Gets or sets the freshness filter for results ("Day", "Week", "Month", or a date range like "2024-01-01..2024-12-31").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? Freshness { get; init; }

    /// <summary>
    /// Gets or sets the safe search level ("Off", "Moderate", or "Strict").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? SafeSearch { get; init; }

    /// <summary>
    /// Gets or sets the 2-character country code for the country where results come from (e.g., "US").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? CountryCode { get; init; }

    /// <summary>
    /// Gets or sets the preferred language to use for user interface strings (e.g., "en").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? SetLanguage { get; init; }

    /// <summary>
    /// Gets or sets a comma-delimited list of answer types to include in the response (e.g., "Webpages,Images").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? ResponseFilter { get; init; }

    /// <summary>
    /// Gets or sets the number of answers that the response should include.
    /// Applied as a default to every search from this instance.
    /// </summary>
    public int? AnswerCount { get; init; }

    /// <summary>
    /// Gets or sets a comma-delimited list of answer types to promote to the mainline (e.g., "Webpages,Videos").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? Promote { get; init; }

    /// <summary>
    /// Gets or sets a value indicating whether to include display string decorations such as hit highlighting markers.
    /// Applied as a default to every search from this instance.
    /// </summary>
    public bool? TextDecorations { get; init; }

    /// <summary>
    /// Gets or sets the type of markers to use for text decorations ("Raw" or "HTML").
    /// Applied as a default to every search from this instance.
    /// </summary>
    public string? TextFormat { get; init; }
}
