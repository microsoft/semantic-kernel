// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Ollama.Core;

/// <summary>
/// Ollama Response object model.
/// </summary>
internal abstract class OllamaResponseBase
{
    /// <summary>
    /// Candidate responses from the model.
    /// </summary>
    [JsonPropertyName("model")]
    public string? Model { get; set; }

    /// <summary>
    /// Returns the prompt's feedback related to the content filters.
    /// </summary>
    [JsonPropertyName("created_at")]
    public DateTime? CreatedAt { get; set; }

    /// <summary>
    /// Returns true when the response is complete.
    /// </summary>
    [JsonPropertyName("done")]
    public bool Done { get; set; }

    /// <summary>
    /// Returns the context tokens returned by the model.
    /// </summary>
    [JsonPropertyName("context")]
    public IReadOnlyList<int>? Context { get; set; }

    /// <summary>
    /// Time spent in nanoseconds generating the response
    /// </summary>
    [JsonPropertyName("total_duration")]
    public long TotalDuration { get; set; }

    /// <summary>
    /// Time spent in nanoseconds loading the model
    /// </summary>
    [JsonPropertyName("load_duration")]
    public long LoadDuration { get; set; }

    /// <summary>
    /// Number of tokens in the prompt
    /// </summary>
    [JsonPropertyName("prompt_eval_count")]
    public int PromptEvalCount { get; set; }

    /// <summary>
    /// Time spent in nanoseconds evaluating the prompt
    /// </summary>
    [JsonPropertyName("prompt_eval_duration")]
    public long PromptEvalDuration { get; set; }

    /// <summary>
    /// Number of tokens the response
    /// </summary>
    [JsonPropertyName("eval_count")]
    public int EvalCount { get; set; }

    /// <summary>
    /// Time in nano seconds spent generating the response
    /// </summary>
    [JsonPropertyName("eval_duration")]
    public long EvalDuration { get; set; }
}
