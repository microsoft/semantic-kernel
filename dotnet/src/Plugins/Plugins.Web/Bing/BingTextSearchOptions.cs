// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Options used to construct an instance of <see cref="BingTextSearch"/>
/// </summary>
public sealed class BingTextSearchOptions
{
    /// <summary>
    /// The URI endpoint of the Bing search service. The URI must use HTTPS.
    /// </summary>
    public string? Endpoint { get; init; } = null;

    /// <summary>
    /// The HTTP client to use for making requests.
    /// </summary>
    public HttpClient? HttpClient { get; init; } = null;

    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; } = null;

    /// <summary>
    ///  Delegate to map a <see cref="BingWebPage"/> instance to a <see cref="string"/>
    /// </summary>
    public MapBingWebPageToString? MapToString { get; init; } = null;

    /// <summary>
    /// Delegate to map a <see cref="BingWebPage"/> instance to a <see cref="TextSearchResult"/>
    /// </summary>
    public MapBingWebPageToTextSearchResult? MapToTextSearchResult { get; init; } = null;
}

/// <summary>
/// Delegate to map a <see cref="BingWebPage"/> instance to a <see cref="string"/>
/// </summary>
public delegate string MapBingWebPageToString(BingWebPage webPage);

/// <summary>
/// Delegate to map a <see cref="BingWebPage"/> instance to a <see cref="TextSearchResult"/>
/// </summary>
public delegate TextSearchResult MapBingWebPageToTextSearchResult(BingWebPage webPage);
