// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Search;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// Options used to construct an instance of <see cref="GoogleTextSearch"/>
/// </summary>
public sealed class GoogleTextSearchOptions
{
    /// <summary>
    /// The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.
    /// </summary>
    public ILoggerFactory? LoggerFactory { get; init; } = null;

    /// <summary>
    ///  Delegate to map a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> instance to a <see cref="string"/>
    /// </summary>
    public MapResultToString? MapToString { get; init; } = null;

    /// <summary>
    /// Delegate to map a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> instance to a <see cref="TextSearchResult"/>
    /// </summary>
    public MapResultToTextSearchResult? MapToTextSearchResult { get; init; } = null;
}

/// <summary>
/// Delegate to map a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> instance to a <see cref="string"/>
/// </summary>
public delegate string MapResultToString(global::Google.Apis.CustomSearchAPI.v1.Data.Result result);

/// <summary>
/// Delegate to map a <see cref="global::Google.Apis.CustomSearchAPI.v1.Data.Result"/> instance to a <see cref="TextSearchResult"/>
/// </summary>
public delegate TextSearchResult MapResultToTextSearchResult(global::Google.Apis.CustomSearchAPI.v1.Data.Result result);
