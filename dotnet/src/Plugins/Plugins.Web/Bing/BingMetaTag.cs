// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Plugins.Web.Bing;

/// <summary>
/// Defines a webpage's metadata.
/// </summary>
public sealed class BingMetaTag
{
    /// <summary>
    /// Only allow creation within this package.
    /// </summary>
    [JsonConstructorAttribute]
    internal BingMetaTag()
    {
    }

    /// <summary>
    /// The metadata.
    /// </summary>
    [JsonPropertyName("content")]
    public string? Content { get; set; }

    /// <summary>
    /// The name of the metadata.
    /// </summary>
    [JsonPropertyName("name")]
    public string? Name { get; set; }
}
