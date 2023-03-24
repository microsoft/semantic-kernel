// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.AI.HuggingFace.HttpSchema;

/// <summary>
/// HTTP schema to perform completion request.
/// </summary>
[Serializable]
public sealed class CompletionRequest
{
    /// <summary>
    /// Prompt to complete.
    /// </summary>
    [JsonPropertyName("prompt")]
    public string Prompt { get; set; } = string.Empty;

    /// <summary>
    /// Model to use for completion.
    /// </summary>
    [JsonPropertyName("model")]
    public string Model { get; set; } = string.Empty;
}
