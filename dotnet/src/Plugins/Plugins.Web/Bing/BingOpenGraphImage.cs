// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Defines the location and dimensions of an image relevant to a webpage.
/// </summary>
public sealed class BingOpenGraphImage
{
    /// <summary>
    /// Only allow creation within this package.
    /// </summary>
    [JsonConstructorAttribute]
    internal BingOpenGraphImage()
    {
    }

    /// <summary>
    /// The image's location.
    /// </summary>
    [JsonPropertyName("contentUrl")]
#pragma warning disable CA1056 // URI-like properties should not be strings
    public string? ContentUrl { get; set; }
#pragma warning restore CA1056 // URI-like properties should not be strings

    /// <summary>
    /// The width of the image. May be zero (0).
    /// </summary>
    [JsonPropertyName("width")]
    public int? Width { get; set; }

    /// <summary>
    /// The height of the image. May be zero (0).
    /// </summary>
    [JsonPropertyName("height")]
    public int? Height { get; set; }
}
