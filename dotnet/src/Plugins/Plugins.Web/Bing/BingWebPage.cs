// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Defines a webpage that is relevant to the query.
/// </summary>
/// TODO: Update this class to match the response from the Bing Web Search API.
/// https://learn.microsoft.com/en-us/bing/search-apis/bing-custom-search/reference/response-objects#webpage
public sealed class BingWebPage
{
    /// <summary>
    /// The last time that Bing crawled the webpage. The date is in the form, YYYY-MM-DDTHH:MM:SS. For example, 2015-04-13T05:23:39.
    /// </summary>
    [JsonPropertyName("dateLastCrawled")]
    public string? DateLastCrawled { get; set; }

    /// <summary>
    /// An ID that uniquely identifies this webpage in the list of web results.
    /// </summary>
    /// <remarks>
    /// The object includes this field only if the Ranking answer specifies that you mix the webpages with the other search results.
    /// Each webpage contains an ID that matches an ID in the Ranking answer. For more information, see Ranking results.
    /// </remarks>
    [JsonPropertyName("id")]
    public string? Id { get; set; }

    /// <summary>
    /// A two-letter language code that identifies the language used by the webpage. For example, the language code is en for English.
    /// </summary>
    [JsonPropertyName("language")]
    public string? Language { get; set; }

    /// <summary>
    /// A Boolean value that indicates whether the webpage contains adult content. If the webpage doesn't contain adult content, isFamilyFriendly is set to true.
    /// </summary>
    [JsonPropertyName("isFamilyFriendly")]
    public bool? IsFamilyFriendly { get; set; }

    /// <summary>
    /// A Boolean value that indicates whether the user’s query is frequently used for navigation to different parts of the webpage’s domain.
    /// Is true if users navigate from this page to other parts of the website.
    /// </summary>
    [JsonPropertyName("isNavigational")]
    public bool? IsNavigational { get; set; }

    /// <summary>
    /// The name of the webpage.
    /// </summary>
    /// <remarks>
    /// Use this name along with url to create a hyperlink that when clicked takes the user to the webpage.
    /// </remarks>
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    /// <summary>
    /// The URL to the webpage.
    /// </summary>
    /// <remarks>
    /// Use this URL along with name to create a hyperlink that when clicked takes the user to the webpage.
    /// </remarks>
    [JsonPropertyName("url")]
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? Url { get; set; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// The display URL of the webpage.
    /// </summary>
    /// <remarks>
    /// The URL is meant for display purposes only and is not well formed.
    /// </remarks>
    [JsonPropertyName("displayUrl")]
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? DisplayUrl { get; set; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// A snippet of text from the webpage that describes its contents.
    /// </summary>
    [JsonPropertyName("snippet")]
    public string? Snippet { get; set; }
}
