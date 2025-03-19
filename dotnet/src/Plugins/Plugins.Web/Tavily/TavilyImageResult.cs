// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Tavily;

internal sealed class TavilyImageResult
{
    /// <summary>
    /// The image url.
    /// </summary>
    [JsonPropertyName("url")]
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
    public TavilyImageResult(string url, string description)
    {
        this.Url = url ?? throw new ArgumentNullException(nameof(url));
        this.Description = description ?? throw new ArgumentNullException(nameof(description));
    }
}
