// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Text to image request
/// </summary>
[Experimental("SKEXP0012")]
public sealed class TextToImageRequest
{
    /// <summary>
    /// Image prompt
    /// </summary>
    [JsonPropertyName("prompt")]
    [JsonPropertyOrder(1)]
    public string Prompt { get; set; } = string.Empty;

    /// <summary>
    /// Image size
    /// </summary>
    [JsonPropertyName("size")]
    [JsonPropertyOrder(2)]
    public string Size { get; set; } = "256x256";

    /// <summary>
    /// How many images to generate
    /// </summary>
    [JsonPropertyName("n")]
    [JsonPropertyOrder(3)]
    public int Count { get; set; } = 1;

    /// <summary>
    /// Image format, "url" or "b64_json"
    /// </summary>
    [JsonPropertyName("response_format")]
    [JsonPropertyOrder(4)]
    public string Format { get; set; } = "url";
}
