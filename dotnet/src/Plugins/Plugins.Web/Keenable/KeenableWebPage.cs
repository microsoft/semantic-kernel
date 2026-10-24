// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Plugins.Web.Keenable;

/// <summary>
/// Represents a type-safe web page result from Keenable search for use with generic ITextSearch&lt;TRecord&gt; interface.
/// This class provides compile-time type safety and IntelliSense support for Keenable search filtering.
/// </summary>
public sealed class KeenableWebPage
{
    /// <summary>
    /// Gets or sets the title of the web page.
    /// </summary>
    public string? Title { get; set; }

    /// <summary>
    /// Gets or sets the URL of the web page.
    /// </summary>
    public Uri? Url { get; set; }

    /// <summary>
    /// Gets or sets the passage of the page text relevant to the query.
    /// </summary>
    public string? Snippet { get; set; }

    /// <summary>
    /// Gets or sets the short description of the web page.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets when the page was published, if known.
    /// </summary>
    public DateTimeOffset? PublishedAt { get; set; }

    /// <summary>
    /// Gets or sets the site filter for search results.
    /// Maps to Keenable's 'site' parameter (e.g., "learn.microsoft.com").
    /// </summary>
    public string? Site { get; set; }

    /// <summary>
    /// Gets or sets the earliest publication date filter for search results.
    /// Maps to Keenable's 'published_after' parameter (YYYY-MM-DD).
    /// </summary>
    public string? PublishedAfter { get; set; }

    /// <summary>
    /// Gets or sets the latest publication date filter for search results.
    /// Maps to Keenable's 'published_before' parameter (YYYY-MM-DD).
    /// </summary>
    public string? PublishedBefore { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KeenableWebPage"/> class.
    /// </summary>
    public KeenableWebPage()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="KeenableWebPage"/> class with specified values.
    /// </summary>
    /// <param name="title">The title of the web page.</param>
    /// <param name="url">The URL of the web page.</param>
    /// <param name="snippet">The passage of the page text relevant to the query.</param>
    /// <param name="description">The short description of the web page.</param>
    /// <param name="publishedAt">When the page was published, if known.</param>
    public KeenableWebPage(string? title, Uri? url, string? snippet, string? description = null, DateTimeOffset? publishedAt = null)
    {
        this.Title = title;
        this.Url = url;
        this.Snippet = snippet;
        this.Description = description;
        this.PublishedAt = publishedAt;
    }

    /// <summary>
    /// Creates a KeenableWebPage from a KeenableSearchResult.
    /// </summary>
    /// <param name="result">The search result to convert.</param>
    /// <returns>A new KeenableWebPage instance.</returns>
    internal static KeenableWebPage FromSearchResult(KeenableSearchResult result)
    {
        Uri? url = string.IsNullOrWhiteSpace(result.Url) ? null : new Uri(result.Url);
        return new KeenableWebPage(result.Title, url, result.Snippet, result.Description, result.PublishedAt);
    }
}
