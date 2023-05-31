// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.OpenAI.ImageGeneration;

/// <summary>
/// Image generation request
/// </summary>
public class AzureImageGenerationRequest
{
    /// <summary>
    /// Image Description
    /// </summary>
    [JsonPropertyName("caption")]
    public string Caption { get; set; } = string.Empty;

    /// <summary>
    /// Image Size
    /// </summary>
    [JsonPropertyName("resolution")]
    public string Resolution { get; set; } = "256x256";
}
