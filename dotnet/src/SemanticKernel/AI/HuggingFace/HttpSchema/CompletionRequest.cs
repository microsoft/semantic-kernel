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
    [JsonPropertyName("inputs")]
    public string Input { get; set; } = string.Empty;
}
