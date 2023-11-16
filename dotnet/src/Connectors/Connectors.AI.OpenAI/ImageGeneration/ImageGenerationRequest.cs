// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Image generation request
/// </summary>
public sealed class ImageGenerationRequest
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

    /// <summary>
    /// The quality of the image that will be generated. Only supported for dall-e-3.
    /// </summary>
    [JsonPropertyName("quality")]
    [JsonPropertyOrder(5)]
    public string? Quality { get; set; }

    /// <summary>
    /// The style of the generated images.  Only supported for dall-e-3.
    /// </summary>
    [JsonPropertyName("style")]
    [JsonPropertyOrder(6)]
    public string? Style { get; set; }

    /// <summary>
    /// The model to use for image generation,Defaults to dall-e-2
    /// </summary>
    [JsonPropertyName("model")]
    [JsonPropertyOrder(7)]
    public string? Model { get; set; }
}
