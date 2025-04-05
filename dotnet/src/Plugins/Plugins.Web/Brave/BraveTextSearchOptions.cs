// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;

/// <summary>
/// Options used to construct an instance of <see cref="BraveTextSearch"/>
/// </summary>
public sealed class BraveTextSearchOptions
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
    /// <see cref="ITextSearchStringMapper" /> instance that can map a <see cref="BraveWebResult"/> to a <see cref="string"/>
    /// </summary>
    public ITextSearchStringMapper? StringMapper { get; init; } = null;

    /// <summary>
    /// <see cref="ITextSearchResultMapper" /> instance that can map a <see cref="BraveWebResult"/> to a <see cref="TextSearchResult"/>
    /// </summary>
    public ITextSearchResultMapper? ResultMapper { get; init; } = null;
}
