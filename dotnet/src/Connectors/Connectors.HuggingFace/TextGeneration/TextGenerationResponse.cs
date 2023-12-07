// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.HuggingFace;

/// <summary>
/// HTTP Schema for completion response.
/// </summary>
public sealed class TextGenerationResponse
{
    /// <summary>
    /// Completed text.
    /// </summary>
    [JsonPropertyName("generated_text")]
    public string? Text { get; set; }
}
