// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.HuggingFace.ImageGeneration;

/// <summary>
/// HTTP schema to perform text-to-image request.
/// </summary>
[Serializable]
public sealed class TextToImageRequest
{
    /// <summary>
    /// Description of image to generate.
    /// </summary>
    [JsonPropertyName("inputs")]
    public string Input { get; set; } = string.Empty;
}
