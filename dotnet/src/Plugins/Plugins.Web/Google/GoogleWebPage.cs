// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Google;

/// <summary>
/// Defines a webpage result from Google Custom Search API.
/// </summary>
public sealed class GoogleWebPage
{
    /// <summary>
    /// Only allow creation within this package.
    /// </summary>
    [JsonConstructorAttribute]
    internal GoogleWebPage()
    {
    }

    /// <summary>
    /// The title of the webpage.
    /// </summary>
    /// <remarks>
    /// Use this title along with Link to create a hyperlink that when clicked takes the user to the webpage.
    /// </remarks>
    [JsonPropertyName("title")]
    public string? Title { get; set; }

    /// <summary>
    /// The URL to the webpage.
    /// </summary>
    /// <remarks>
    /// Use this URL along with Title to create a hyperlink that when clicked takes the user to the webpage.
    /// </remarks>
    [JsonPropertyName("link")]
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? Link { get; set; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// A snippet of text from the webpage that describes its contents.
    /// </summary>
    [JsonPropertyName("snippet")]
    public string? Snippet { get; set; }

    /// <summary>
    /// The formatted URL display string.
    /// </summary>
    /// <remarks>
    /// The URL is meant for display purposes only and may not be well formed.
    /// </remarks>
    [JsonPropertyName("displayLink")]
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? DisplayLink { get; set; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// The MIME type of the result.
    /// </summary>
    [JsonPropertyName("mime")]
    public string? Mime { get; set; }

    /// <summary>
    /// The file format of the result.
    /// </summary>
    [JsonPropertyName("fileFormat")]
    public string? FileFormat { get; set; }

    /// <summary>
    /// The HTML title of the webpage.
    /// </summary>
    [JsonPropertyName("htmlTitle")]
    public string? HtmlTitle { get; set; }

    /// <summary>
    /// The HTML snippet of the webpage.
    /// </summary>
    [JsonPropertyName("htmlSnippet")]
    public string? HtmlSnippet { get; set; }

    /// <summary>
    /// The formatted URL of the webpage.
    /// </summary>
    [JsonPropertyName("formattedUrl")]
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? FormattedUrl { get; set; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// The HTML-formatted URL of the webpage.
    /// </summary>
    [JsonPropertyName("htmlFormattedUrl")]
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? HtmlFormattedUrl { get; set; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// Labels associated with the webpage.
    /// </summary>
    [JsonPropertyName("labels")]
    public IReadOnlyList<string>? Labels { get; set; }
}
