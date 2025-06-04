// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

#pragma warning disable CA1812 // Instantiated by reflection
/// <summary>
/// Bing search response.
/// </summary>
internal sealed class BingSearchResponse<T>
{
    /// <summary>
    /// Type hint, which is set to SearchResponse.
    /// </summary>
    [JsonPropertyName("_type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// The query string that Bing used for the request.
    /// </summary>
    [JsonPropertyName("queryContext")]
    public BingQueryContext? QueryContext { get; set; }

    /// <summary>
    /// A nullable WebAnswer object containing the Web Search API response data.
    /// </summary>
    [JsonPropertyName("webPages")]
    public BingWebPages<T>? WebPages { get; set; }
}

/// <summary>
/// The query string that Bing used for the request.
/// </summary>
internal sealed class BingQueryContext
{
    /// <summary>
    /// The query string as specified in the request.
    /// </summary>
    [JsonPropertyName("originalQuery")]
    public string OriginalQuery { get; set; } = string.Empty;

    /// <summary>
    /// The query string that Bing used to perform the query. Bing uses the altered query string if the original query string contained spelling mistakes.
    /// For example, if the query string is saling downwind, the altered query string is sailing downwind.
    /// </summary>
    /// <remarks>
    /// The object includes this field only if the original query string contains a spelling mistake.
    /// </remarks>
    [JsonPropertyName("alteredQuery")]
    public string? AlteredQuery { get; set; }
}

/// <summary>
/// A list of webpages that are relevant to the search query.
/// </summary>
#pragma warning disable CA1056 // A constant Uri cannot be defined, as required by this class
internal sealed class BingWebPages<T>
{
    /// <summary>
    /// An ID that uniquely identifies the web answer.
    /// </summary>
    /// <remarks>
    /// The object includes this field only if the Ranking answer suggests that you display all web results in a group. For more information about how to use the ID, see Ranking results.
    /// </remarks>
    [JsonPropertyName("id")]
    public string Id { get; set; } = string.Empty;

    /// <summary>
    /// A Boolean value that indicates whether the response excluded some results from the answer. If Bing excluded some results, the value is true.
    /// </summary>
    [JsonPropertyName("someResultsRemoved")]
    public bool SomeResultsRemoved { get; set; }

    /// <summary>
    /// The estimated number of webpages that are relevant to the query. Use this number along with the count and offset query parameters to page the results.
    /// </summary>
    [JsonPropertyName("totalEstimatedMatches")]
    public long TotalEstimatedMatches { get; set; }

    /// <summary>
    /// The URL to the Bing search results for the requested webpages.
    /// </summary>
    [JsonPropertyName("webSearchUrl")]
    public string WebSearchUrl { get; set; } = string.Empty;

    /// <summary>
    /// A list of webpages that are relevant to the query.
    /// </summary>
    [JsonPropertyName("value")]
    public IList<T>? Value { get; set; }
}
#pragma warning restore CA1056
#pragma warning restore CA1812
