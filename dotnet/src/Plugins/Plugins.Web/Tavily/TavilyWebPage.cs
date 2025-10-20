// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// Represents a type-safe web page result from Tavily search for use with generic ITextSearch&lt;TRecord&gt; interface.
/// This class provides compile-time type safety and IntelliSense support for Tavily search filtering.
/// </summary>
public sealed class TavilyWebPage
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
    /// Gets or sets the content/description of the web page.
    /// </summary>
    public string? Content { get; set; }

    /// <summary>
    /// Gets or sets the raw content of the web page (if available).
    /// </summary>
    public string? RawContent { get; set; }

    /// <summary>
    /// Gets or sets the relevance score of the search result.
    /// </summary>
    public double Score { get; set; }

    /// <summary>
    /// Gets or sets the topic filter for search results.
    /// Maps to Tavily's 'topic' parameter for focused search.
    /// </summary>
    public string? Topic { get; set; }

    /// <summary>
    /// Gets or sets the time range filter for search results.
    /// Maps to Tavily's 'time_range' parameter (e.g., "day", "week", "month", "year").
    /// </summary>
    public string? TimeRange { get; set; }

    /// <summary>
    /// Gets or sets the number of days for time-based filtering.
    /// Maps to Tavily's 'days' parameter for custom date ranges.
    /// </summary>
    public int? Days { get; set; }

    /// <summary>
    /// Gets or sets the domain to include in search results.
    /// Maps to Tavily's 'include_domain' parameter.
    /// </summary>
    public string? IncludeDomain { get; set; }

    /// <summary>
    /// Gets or sets the domain to exclude from search results.
    /// Maps to Tavily's 'exclude_domain' parameter.
    /// </summary>
    public string? ExcludeDomain { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TavilyWebPage"/> class.
    /// </summary>
    public TavilyWebPage()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="TavilyWebPage"/> class with specified values.
    /// </summary>
    /// <param name="title">The title of the web page.</param>
    /// <param name="url">The URL of the web page.</param>
    /// <param name="content">The content/description of the web page.</param>
    /// <param name="score">The relevance score.</param>
    /// <param name="rawContent">The raw content (optional).</param>
    public TavilyWebPage(string? title, Uri? url, string? content, double score, string? rawContent = null)
    {
        this.Title = title;
        this.Url = url;
        this.Content = content;
        this.Score = score;
        this.RawContent = rawContent;
    }

    /// <summary>
    /// Creates a TavilyWebPage from a TavilySearchResult.
    /// </summary>
    /// <param name="result">The search result to convert.</param>
    /// <returns>A new TavilyWebPage instance.</returns>
    internal static TavilyWebPage FromSearchResult(TavilySearchResult result)
    {
        Uri? url = string.IsNullOrWhiteSpace(result.Url) ? null : new Uri(result.Url);
        return new TavilyWebPage(result.Title, url, result.Content, result.Score, result.RawContent);
    }
}
