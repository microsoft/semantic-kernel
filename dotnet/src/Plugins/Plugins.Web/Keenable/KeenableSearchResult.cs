// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Keenable;

/// <summary>
/// Represents a search result from Keenable.
/// </summary>
[System.Diagnostics.CodeAnalysis.SuppressMessage("Design", "CA1056:URI-like properties should not be strings", Justification = "API definition")]
public sealed class KeenableSearchResult
{
    /// <summary>
    /// Only allow creation within this package.
    /// </summary>
    [JsonConstructor]
    internal KeenableSearchResult()
    {
    }

    /// <summary>
    /// The title of the page.
    /// </summary>
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// The URL of the page.
    /// </summary>
    [JsonPropertyName("url")]
    public string Url { get; set; } = string.Empty;

    /// <summary>
    /// A passage of the page text relevant to the query. This is the main text field of a result.
    /// </summary>
    [JsonPropertyName("snippet")]
    public string? Snippet { get; set; }

    /// <summary>
    /// A short description of the page. May be empty; prefer <see cref="Snippet"/>.
    /// </summary>
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>
    /// When the page was published, if known.
    /// </summary>
    [JsonPropertyName("published_at")]
    public DateTimeOffset? PublishedAt { get; set; }

    /// <summary>
    /// Additional properties that are not explicitly defined in the schema.
    /// </summary>
    [JsonExtensionData]
    public IDictionary<string, object> AdditionalProperties { get; set; } = new Dictionary<string, object>();

    /// <summary>
    /// The text to use for this result: the snippet, or the description when the snippet is empty.
    /// </summary>
    internal string Text => string.IsNullOrEmpty(this.Snippet) ? this.Description ?? string.Empty : this.Snippet!;
}
