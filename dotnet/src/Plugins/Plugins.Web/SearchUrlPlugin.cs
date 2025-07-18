// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Text.Encodings.Web;

namespace Microsoft.SemanticKernel.Plugins.Web;

/// <summary>
/// Get search URLs for various websites
/// </summary>
[SuppressMessage("Design", "CA1055:URI return values should not be strings", Justification = "Semantic Kernel operates on strings")]
public sealed class SearchUrlPlugin
{
    /**
     * Amazon Search URLs
     */
    /// <summary>
    /// Get search URL for Amazon
    /// </summary>
    [KernelFunction, Description("Return URL for Amazon search query")]
    public string AmazonSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.amazon.com/s?k={encoded}";
    }

    /**
     * Bing Search URLs
     */
    /// <summary>
    /// Get search URL for Bing
    /// </summary>
    [KernelFunction, Description("Return URL for Bing search query.")]
    public string BingSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/search?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Images
    /// </summary>
    [KernelFunction, Description("Return URL for Bing Images search query.")]
    public string BingImagesSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/images/search?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Maps
    /// </summary>
    [KernelFunction, Description("Return URL for Bing Maps search query.")]
    public string BingMapsSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/maps?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Shopping
    /// </summary>
    [KernelFunction, Description("Return URL for Bing Shopping search query.")]
    public string BingShoppingSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/shop?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing News
    /// </summary>
    [KernelFunction, Description("Return URL for Bing News search query.")]
    public string BingNewsSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/news/search?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Travel
    /// </summary>
    [KernelFunction, Description("Return URL for Bing Travel search query.")]
    public string BingTravelSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/travel/search?q={encoded}";
    }

    /**
    * Brave Search URLSs
    **/
    /// <summary>
    /// Get search URL for Brave
    /// </summary>
    [KernelFunction, Description("Return URL for Brave search query.")]
    public string BraveSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://search.brave.com/search?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Brave Images
    /// </summary>
    [KernelFunction, Description("Return URL for Brave Images search query.")]
    public string BraveImagesSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://search.brave.com/images?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Brave News
    /// </summary>
    [KernelFunction, Description("Return URL for Brave News search query.")]
    public string BraveNewsSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://search.brave.com/news?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Brave Googles
    /// </summary>
    [KernelFunction, Description("Return URL for Brave Googles search query.")]
    public string BraveGooglesSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://search.brave.com/goggles?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Brave Videos
    /// </summary>
    [KernelFunction, Description("Return URL for Brave Videos search query.")]
    public string BraveVideosSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://search.brave.com/videos?q={encoded}";
    }

    /**
     * Facebook Search URLs
     */
    /// <summary>
    /// Get search URL for Facebook
    /// </summary>
    [KernelFunction, Description("Return URL for Facebook search query.")]
    public string FacebookSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.facebook.com/search/top/?q={encoded}";
    }

    /**
     * GitHub Search URLs
     */
    /// <summary>
    /// Get search URL for GitHub
    /// </summary>
    [KernelFunction, Description("Return URL for GitHub search query.")]
    public string GitHubSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://github.com/search?q={encoded}";
    }

    /**
     * LinkedIn Search URLs
     */
    /// <summary>
    /// Get search URL for LinkedIn
    /// </summary>
    [KernelFunction, Description("Return URL for LinkedIn search query.")]
    public string LinkedInSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.linkedin.com/search/results/index/?keywords={encoded}";
    }

    /**
     * Twitter Search URLs
     */
    /// <summary>
    /// Get search URL for Twitter
    /// </summary>
    [KernelFunction, Description("Return URL for Twitter search query.")]
    public string TwitterSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://twitter.com/search?q={encoded}";
    }

    /**
     * Wikipedia Search URLs
     */
    /// <summary>
    /// Get search URL for Wikipedia
    /// </summary>
    [KernelFunction, Description("Return URL for Wikipedia search query.")]
    public string WikipediaSearchUrl([Description("Text to search for")] string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://wikipedia.org/w/index.php?search={encoded}";
    }
}
