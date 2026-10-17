// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Keenable;

/// <summary>
/// Request body sent to the Keenable search API.
/// </summary>
internal sealed class KeenableSearchRequest
{
    /// <summary>
    /// The search query to execute.
    /// </summary>
    [JsonPropertyName("query")]
    [JsonRequired]
    public string Query { get; set; }

    /// <summary>
    /// The maximum number of search results to return.
    /// Required range: 1 - 50
    /// </summary>
    [JsonPropertyName("max_results")]
    public int? MaxResults { get; set; }

    /// <summary>
    /// Requested maximum length, in characters, of each result snippet. Treated as a hint by the service.
    /// </summary>
    [JsonPropertyName("snippet_max_length")]
    public int? SnippetMaxLength { get; set; }

    /// <summary>
    /// Restrict results to pages published on or after this date (YYYY-MM-DD).
    /// </summary>
    [JsonPropertyName("published_after")]
    public string? PublishedAfter { get; set; }

    /// <summary>
    /// Restrict results to pages published on or before this date (YYYY-MM-DD).
    /// </summary>
    [JsonPropertyName("published_before")]
    public string? PublishedBefore { get; set; }

    /// <summary>
    /// Restrict results to a single site, e.g. "learn.microsoft.com".
    /// </summary>
    [JsonPropertyName("site")]
    public string? Site { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KeenableSearchRequest" /> class.
    /// </summary>
    public KeenableSearchRequest(
        string query,
        int? maxResults,
        int? snippetMaxLength,
        string? publishedAfter,
        string? publishedBefore,
        string? site)
    {
        this.Query = query ?? throw new ArgumentNullException(nameof(query));
        this.MaxResults = maxResults;
        this.SnippetMaxLength = snippetMaxLength;
        this.PublishedAfter = publishedAfter;
        this.PublishedBefore = publishedBefore;
        this.Site = site;
    }
}
