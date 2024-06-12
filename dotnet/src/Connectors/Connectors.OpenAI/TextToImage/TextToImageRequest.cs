// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Text to image request
/// </summary>
internal sealed class TextToImageRequest
{
    /// <summary>
    /// Model to use for image generation
    /// </summary>
    [JsonPropertyName("model")]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? Model { get; set; }

    /// <summary>
    /// Image prompt
    /// </summary>
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; } = string.Empty;

    /// <summary>
    /// Image size
    /// </summary>
    [JsonPropertyName("size")]
    public string Size { get; set; } = "256x256";

    /// <summary>
    /// How many images to generate
    /// </summary>
    [JsonPropertyName("n")]
    public int Count { get; set; } = 1;

    /// <summary>
    /// Image format, "url" or "b64_json"
    /// </summary>
    [JsonPropertyName("response_format")]
    public string Format { get; set; } = "url";
}
