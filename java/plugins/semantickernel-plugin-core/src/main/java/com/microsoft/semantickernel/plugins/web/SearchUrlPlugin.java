// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.plugins.web;

import com.microsoft.semantickernel.semanticfunctions.annotations.DefineKernelFunction;
import com.microsoft.semantickernel.semanticfunctions.annotations.KernelFunctionParameter;
import java.io.UnsupportedEncodingException;
import java.net.URLEncoder;

public class SearchUrlPlugin {
    /*
     * Amazon Search URLs
     */
    /// <summary>
    /// Get search URL for Amazon
    /// </summary>
    @DefineKernelFunction(name = "AmazonSearchUrl", description = "Return URL for Amazon search query")
    public String AmazonSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.amazon.com/s?k=%s", encoded);
    }

    /*
     * Bing Search URLs
     */
    /// <summary>
    /// Get search URL for Bing
    /// </summary>
    @DefineKernelFunction(name = "BingSearchUrl", description = "Return URL for Bing search query.")
    public String BingSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.bing.com/search?q=%s", encoded);
    }

    /// <summary>
    /// Get search URL for Bing Images
    /// </summary>
    @DefineKernelFunction(name = "BingImagesSearchUrl", description = "Return URL for Bing Images search query.")
    public String BingImagesSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.bing.com/images/search?q=%s", encoded);
    }

    /// <summary>
    /// Get search URL for Bing Maps
    /// </summary>
    @DefineKernelFunction(name = "BingMapsSearchUrl", description = "Return URL for Bing Maps search query.")
    public String BingMapsSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.bing.com/maps?q=%s", encoded);
    }

    /// <summary>
    /// Get search URL for Bing Shopping
    /// </summary>
    @DefineKernelFunction(name = "BingShoppingSearchUrl", description = "Return URL for Bing Shopping search query.")
    public String BingShoppingSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.bing.com/shop?q=%s", encoded);
    }

    /// <summary>
    /// Get search URL for Bing News
    /// </summary>
    @DefineKernelFunction(name = "BingNewsSearchUrl", description = "Return URL for Bing News search query.")
    public String BingNewsSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.bing.com/news/search?q=%s", encoded);
    }

    /// <summary>
    /// Get search URL for Bing Travel
    /// </summary>
    @DefineKernelFunction(name = "BingTravelSearchUrl", description = "Return URL for Bing Travel search query.")
    public String BingTravelSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.bing.com/travel/search?q=%s", encoded);
    }

    /*
     * Facebook Search URLs
     */
    /// <summary>
    /// Get search URL for Facebook
    /// </summary>
    @DefineKernelFunction(name = "FacebookSearchUrl", description = "Return URL for Facebook search query.")
    public String FacebookSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.facebook.com/search/top/?q=%s", encoded);
    }

    /*
     * GitHub Search URLs
     */
    /// <summary>
    /// Get search URL for GitHub
    /// </summary>
    @DefineKernelFunction(name = "GitHubSearchUrl", description = "Return URL for GitHub search query.")
    public String GitHubSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://github.com/search?q=%s", encoded);
    }

    /*
     * LinkedIn Search URLs
     */
    /// <summary>
    /// Get search URL for LinkedIn
    /// </summary>
    @DefineKernelFunction(name = "LinkedInSearchUrl", description = "Return URL for LinkedIn search query.")
    public String LinkedInSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://www.linkedin.com/search/results/index/?keywords=%s", encoded);
    }

    /*
     * Twitter Search URLs
     */
    /// <summary>
    /// Get search URL for Twitter
    /// </summary>
    @DefineKernelFunction(name = "TwitterSearchUrl", description = "Return URL for Twitter search query.")
    public String TwitterSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://twitter.com/search?q=%s", encoded);
    }

    /*
     * Wikipedia Search URLs
     */
    /// <summary>
    /// Get search URL for Wikipedia
    /// </summary>
    @DefineKernelFunction(name = "WikipediaSearchUrl", description = "Return URL for Wikipedia search query.")
    public String WikipediaSearchUrl(
        @KernelFunctionParameter(description = "Text to search for", name = "query", required = true, type = String.class) String query) {
        String encoded = encode(query);
        return String.format("https://wikipedia.org/w/index.php?search=%s", encoded);
    }

    private static String encode(String query) {
        try {
            return URLEncoder.encode(query, "UTF-8");
        } catch (UnsupportedEncodingException e) {
            // should never happen since UTF-8 is always supported
            return query;
        }
    }
}
