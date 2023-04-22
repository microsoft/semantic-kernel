// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Encodings.Web;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Web;

/// <summary>
/// Get search URLs for various websites
/// </summary>
[SuppressMessage("Design", "CA1055:URI return values should not be strings", Justification = "Semantic Kernel operates on strings")]
public class SearchUrlSkill
{
    /**
     * Amazon Search URLs
     */
    /// <summary>
    /// Get search URL for Amazon
    /// </summary>
    [SKFunction("Return URL for Amazon search query")]
    public string AmazonSearchUrl(string query)
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
    [SKFunction("Return URL for Bing search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string BingSearchUrl(string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/search?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Images
    /// </summary>
    [SKFunction("Return URL for Bing Images search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string BingImagesSearchUrl(string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/images/search?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Maps
    /// </summary>
    [SKFunction("Return URL for Bing Maps search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string BingMapsSearchUrl(string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/maps?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Shopping
    /// </summary>
    [SKFunction("Return URL for Bing Shopping search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string BingShoppingSearchUrl(string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/shop?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing News
    /// </summary>
    [SKFunction("Return URL for Bing News search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string BingNewsSearchUrl(string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/news/search?q={encoded}";
    }

    /// <summary>
    /// Get search URL for Bing Travel
    /// </summary>
    [SKFunction("Return URL for Bing Travel search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string BingTravelSearchUrl(string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://www.bing.com/travel/search?q={encoded}";
    }

    /**
     * Facebook Search URLs
     */
    /// <summary>
    /// Get search URL for Facebook
    /// </summary>
    [SKFunction("Return URL for Facebook search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string FacebookSearchUrl(string query)
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
    [SKFunction("Return URL for GitHub search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string GitHubSearchUrl(string query)
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
    [SKFunction("Return URL for LinkedIn search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string LinkedInSearchUrl(string query)
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
    [SKFunction("Return URL for Twitter search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string TwitterSearchUrl(string query)
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
    [SKFunction("Return URL for Wikipedia search query.")]
    [SKFunctionInput(Description = "Text to search for")]
    public string WikipediaSearchUrl(string query)
    {
        string encoded = UrlEncoder.Default.Encode(query);
        return $"https://wikipedia.org/w/index.php?search={encoded}";
    }
}
