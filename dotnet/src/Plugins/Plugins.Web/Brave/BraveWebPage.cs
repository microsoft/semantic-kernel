// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Plugins.Web.Brave;

/// <summary>
/// Represents a type-safe web page result from Brave search for use with generic ITextSearch&lt;TRecord&gt; interface.
/// This class provides compile-time type safety and IntelliSense support for Brave search filtering.
/// </summary>
public sealed class BraveWebPage
{
    /// <summary>
    /// Gets or sets the title of the web page.
    /// </summary>
    public string? Title { get; set; }

    /// <summary>
    /// Gets or sets the URL of the web page.
    /// </summary>
    public string? Url { get; set; }

    /// <summary>
    /// Gets or sets the description of the web page.
    /// </summary>
    public string? Description { get; set; }

    /// <summary>
    /// Gets or sets the type of the search result.
    /// </summary>
    public string? Type { get; set; }

    /// <summary>
    /// Gets or sets the age of the web search result.
    /// </summary>
    public string? Age { get; set; }

    /// <summary>
    /// Gets or sets the page age timestamp.
    /// </summary>
    public DateTime? PageAge { get; set; }

    /// <summary>
    /// Gets or sets the language of the web page.
    /// </summary>
    public string? Language { get; set; }

    /// <summary>
    /// Gets or sets whether the web page is family friendly.
    /// </summary>
    public bool? FamilyFriendly { get; set; }

    /// <summary>
    /// Gets or sets the country filter for search results.
    /// Maps to Brave's 'country' parameter (e.g., "US", "GB", "CA").
    /// </summary>
    public string? Country { get; set; }

    /// <summary>
    /// Gets or sets the search language filter.
    /// Maps to Brave's 'search_lang' parameter (e.g., "en", "es", "fr").
    /// </summary>
    public string? SearchLang { get; set; }

    /// <summary>
    /// Gets or sets the UI language filter.
    /// Maps to Brave's 'ui_lang' parameter (e.g., "en-US", "en-GB").
    /// </summary>
    public string? UiLang { get; set; }

    /// <summary>
    /// Gets or sets the safe search filter.
    /// Maps to Brave's 'safesearch' parameter ("off", "moderate", "strict").
    /// </summary>
    public string? SafeSearch { get; set; }

    /// <summary>
    /// Gets or sets whether text decorations are enabled.
    /// Maps to Brave's 'text_decorations' parameter.
    /// </summary>
    public bool? TextDecorations { get; set; }

    /// <summary>
    /// Gets or sets whether spell check is enabled.
    /// Maps to Brave's 'spellcheck' parameter.
    /// </summary>
    public bool? SpellCheck { get; set; }

    /// <summary>
    /// Gets or sets the result filter for search types.
    /// Maps to Brave's 'result_filter' parameter (e.g., "web", "news", "videos").
    /// </summary>
    public string? ResultFilter { get; set; }

    /// <summary>
    /// Gets or sets the units system for measurements.
    /// Maps to Brave's 'units' parameter ("metric" or "imperial").
    /// </summary>
    public string? Units { get; set; }

    /// <summary>
    /// Gets or sets whether extra snippets are included.
    /// Maps to Brave's 'extra_snippets' parameter.
    /// </summary>
    public bool? ExtraSnippets { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="BraveWebPage"/> class.
    /// </summary>
    public BraveWebPage()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="BraveWebPage"/> class with specified values.
    /// </summary>
    /// <param name="title">The title of the web page.</param>
    /// <param name="url">The URL of the web page.</param>
    /// <param name="description">The description of the web page.</param>
    /// <param name="type">The type of the search result.</param>
    public BraveWebPage(string? title, string? url, string? description, string? type = null)
    {
        this.Title = title;
        this.Url = url;
        this.Description = description;
        this.Type = type;
    }

    /// <summary>
    /// Creates a BraveWebPage from a BraveWebResult.
    /// </summary>
    /// <param name="result">The web result to convert.</param>
    /// <returns>A new BraveWebPage instance.</returns>
    internal static BraveWebPage FromWebResult(BraveWebResult result)
    {
        return new BraveWebPage(result.Title, result.Url, result.Description, result.Type)
        {
            Age = result.Age,
            PageAge = result.PageAge,
            Language = result.Language,
            FamilyFriendly = result.FamilyFriendly
        };
    }
}
