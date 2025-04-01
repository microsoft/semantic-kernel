// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// Represents a search result from Tavily.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1056:URI-like properties should not be strings", Justification = "API definition")]
public sealed class TavilySearchResult
{
    /// <summary>
    /// The title of the search result.
    /// </summary>
    [JsonPropertyName("title")]
    [JsonRequired]
    public string Title { get; set; }

    /// <summary>
    ///The URL of the search result.
    /// </summary>
    [JsonPropertyName("url")]
    [JsonRequired]
    public string Url { get; set; }

    /// <summary>
    /// A short description of the search result.
    /// </summary>
    [JsonPropertyName("content")]
    [JsonRequired]
    public string Content { get; set; }

    /// <summary>
    /// The cleaned and parsed HTML content of the search result. Only if include_raw_content is true.
    /// </summary>
    [JsonPropertyName("raw_content")]
    public string? RawContent { get; set; }

    /// <summary>
    /// The relevance score of the search result.
    /// </summary>
    [JsonPropertyName("score")]
    [JsonRequired]
    public double Score { get; set; }

    /// <summary>
    /// Additional properties that are not explicitly defined in the schema
    /// </summary>
    [JsonExtensionData]
    public IDictionary<string, object> AdditionalProperties { get; set; } = new Dictionary<string, object>();

    /// <summary>
    /// Initializes a new instance of the <see cref="TavilySearchResult" /> class.
    /// </summary>
    public TavilySearchResult(
        string title,
#pragma warning disable CA1054 // URI-like parameters should not be strings
        string url,
#pragma warning restore CA1054 // URI-like parameters should not be strings
        string content,
        double score,
        string? rawContent)
    {
        this.Title = title ?? throw new ArgumentNullException(nameof(title));
        this.Url = url ?? throw new ArgumentNullException(nameof(url));
        this.Content = content ?? throw new ArgumentNullException(nameof(content));
        this.Score = score;
        this.RawContent = rawContent;
    }
}
