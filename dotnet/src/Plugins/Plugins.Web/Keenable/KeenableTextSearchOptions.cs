// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Plugins.Web.Keenable;

/// <summary>
/// Options used to construct an instance of <see cref="KeenableTextSearch"/>.
/// </summary>
public sealed class KeenableTextSearchOptions
{
    /// <summary>
    /// The base URI of the Keenable search service. The URI must use HTTPS; any other scheme is rejected when the search instance is created.
    /// The connector appends <c>/v1/search</c> when an API key is configured and <c>/v1/search/public</c> otherwise.
    /// Defaults to <c>https://api.keenable.ai</c>.
    /// </summary>
    public Uri? Endpoint { get; init; } = null;

    /// <summary>
    /// Requested maximum length, in characters, of the snippet returned for each result.
    /// The service treats this as a hint. When null the service default is used.
    /// </summary>
    public int? SnippetMaxLength { get; set; }

    /// <summary>
    /// The HTTP client to use for making requests.
    /// </summary>
    public HttpClient? HttpClient { get; init; } = null;

    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchStringMapper" /> instance that can map a <see cref="KeenableSearchResult"/> to a <see cref="string"/>
    /// </summary>
    public ITextSearchStringMapper? StringMapper { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchResultMapper" /> instance that can map a <see cref="KeenableSearchResult"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    public ITextSearchResultMapper? ResultMapper { get; init; } = null;
}
