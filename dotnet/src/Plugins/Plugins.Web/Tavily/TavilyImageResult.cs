// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

/// <summary>
/// Represents an image result.
/// </summary>
#pragma warning disable CA1812 // Instantiated by reflection
internal sealed class TavilyImageResult
{
    /// <summary>
    /// The image url.
    /// </summary>
    [JsonPropertyName("url")]
    [JsonRequired]
    public string Url { get; set; }

    /// <summary>
    /// The image description.
    /// </summary>
    [JsonPropertyName("description")]
    [JsonRequired]
    public string Description { get; set; }

    /// <summary>
    /// Initializes a new instance of the <see cref="TavilyImageResult" /> class.
    /// </summary>
    /// <param name="url">The url to the image</param>
    /// <param name="description">The description of the image</param>
    /// <exception cref="ArgumentNullException"></exception>
#pragma warning disable CA1054 // URI-like parameters should not be strings
    public TavilyImageResult(string url, string description)
#pragma warning restore CA1054 // URI-like parameters should not be strings
    {
        this.Url = url ?? throw new ArgumentNullException(nameof(url));
        this.Description = description ?? throw new ArgumentNullException(nameof(description));
    }
}
#pragma warning restore CA1812 // Instantiated by reflection
