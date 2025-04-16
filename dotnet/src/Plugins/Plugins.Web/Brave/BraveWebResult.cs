// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;

/// <summary>
/// The Brave Web Page Response
/// </summary>
/// <remarks>Can be use for parse for SearchResult LocationResult VideoResult NewsResult</remarks>
public sealed class BraveWebResult
{
    /// <summary>
    /// Only allow creation within this package.
    /// </summary>
    [JsonConstructor]
    internal BraveWebResult()
    {
    }

    /// <summary>
    /// A type identifying a web search result.
    /// </summary>
    [JsonPropertyName("type")]
    public string Type { get; set; } = string.Empty;

    /// <summary>
    /// The url link where the page is served.
    /// </summary>
    [JsonPropertyName("url")]
#pragma warning disable CA1056
    public string Url { get; set; } = string.Empty;
#pragma warning restore CA1056

    /// <summary>
    /// The title of the web page.
    /// </summary>
    [JsonPropertyName("title")]
    public string Title { get; set; } = string.Empty;

    /// <summary>
    /// A description for the web page.
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// A string representing the age of the web search result.
    /// </summary>
    [JsonPropertyName("age")]
    public string Age { get; set; } = string.Empty;

    /// <summary>
    /// Whether the news result is currently a breaking news.
    /// </summary>
    [JsonPropertyName("breaking")]
    public bool? Breaking { get; set; }

    /// <summary>
    /// Whether the news result is currently a breaking news.
    /// </summary>
    [JsonPropertyName("page_age")]
    public DateTime? PageAge { get; set; }

    /// <summary>
    /// The video associated with the web search result.
    /// </summary>
    [JsonPropertyName("video")]
    public BraveVideo? Video { get; set; }

    /// <summary>
    /// Aggregated information on the url associated with the web search result.
    /// </summary>
    [JsonPropertyName("meta_url")]
    public MetaUrl? MetaUrl { get; set; }

    /// <summary>
    /// The thumbnail of the web search result.
    /// </summary>
    [JsonPropertyName("thumbnail")]
    public Thumbnail? Thumbnail { get; set; }

    /// <summary>
    /// Result Source
    /// </summary>
    [JsonPropertyName("source")]
    public string? Source { get; set; }

    /// <summary>
    /// Is source is local
    /// </summary>
    [JsonPropertyName("is_source_local")]
    public bool? IsSourceLocal { get; set; }

    /// <summary>
    /// Is Source Both
    /// </summary>
    [JsonPropertyName("is_source_both")]
    public bool? IsSourceBoth { get; set; }

    /// <summary>
    /// A profile associated with the web page.
    /// </summary>
    [JsonPropertyName("profile")]
    public BraveProfile? Profile { get; set; }

    /// <summary>
    /// A language classification for the web page.
    /// </summary>
    [JsonPropertyName("language")]
    public string? Language { get; set; }

    /// <summary>
    /// Whether the web page is family friendly.
    /// </summary>
    [JsonPropertyName("family_friendly")]
    public bool? FamilyFriendly { get; set; }

    /// <summary>
    /// A subtype identifying the web search result type.
    /// </summary>
    [JsonPropertyName("subtype")]
    public string? Subtype { get; set; }

    /// <summary>
    /// Whether the web search result is currently live. Default value is False.
    /// </summary>
    [JsonPropertyName("is_live")]
    public bool? IsLive { get; set; }

    /// <summary>
    /// A list of extra alternate snippets for the news search result.
    /// </summary>
    [JsonPropertyName("extra_snippets")]
    public List<string>? ExtraSnippets { get; set; }

    /// <summary>
    /// Gathered information on a web search result.
    /// </summary>
    [JsonPropertyName("deep_results")]
    public DeepResults? DeepResults { get; set; }
}
