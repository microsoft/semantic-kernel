// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.PaLM.TextCompletion;

/// <summary>
/// HTTP schema to perform completion request.
/// </summary>
[Serializable]
public sealed class TextCompletionRequest
{
    ///// <summary>
    ///// Prompt to complete.
    ///// </summary>
    //[JsonPropertyName("inputs")]
    //public string Input { get; set; } = string.Empty;
    public Prompt prompt { get; set; } = new();
    public float temperature { get; set; } = 0.1f;
    public float top_p { get; set; } = 0.95f;
    public int candidate_count { get; set; } = 3;
    public int top_k { get; set; } = 40;
    public int max_output_tokens { get; set; } = 2048;
    public string[] stop_sequences { get; set; } = Array.Empty<string>();
}

public class Prompt
{
    public string text { get; set; } = string.Empty;
}
