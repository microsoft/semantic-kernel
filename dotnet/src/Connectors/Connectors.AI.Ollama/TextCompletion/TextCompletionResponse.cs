// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;

/// <summary>
/// HTTP Schema for completion response.
/// </summary>
public sealed class TextCompletionResponse
{
    /// <summary>
    /// Time spent generating the response
    /// </summary>
    [JsonPropertyName("total_duration")]
    public long TotalDuration { get; set; }

    /// <summary>
    /// Time spent in nanoseconds loading the model
    /// </summary>
    [JsonPropertyName("load_duration")]
    public long LoadDuration { get; set; }

    /// <summary>
    /// Number of samples generated
    /// </summary>
    [JsonPropertyName("sample_count")]
    public int SampleCount { get; set; }

    /// <summary>
    /// Time spent generating samples
    /// </summary>
    [JsonPropertyName("sample_duration")]
    public long SampleDuration { get; set; }

    /// <summary>
    /// Number of tokens in the prompt
    /// </summary>
    [JsonPropertyName("prompt_eval_count")]
    public int PromptEvalCount { get; set; }

    /// <summary>
    /// Time spent in nanoseconds evaluating the prompt
    /// </summary>
    [JsonPropertyName("prompt_eval_duration")]
    public int PromptEvalDuration { get; set; }

    /// <summary>
    /// Number of tokens the response
    /// </summary>
    [JsonPropertyName("eval_count")]
    public int EvalCount { get; set; }

    /// <summary>
    /// Time in nanoseconds spent generating the response
    /// </summary>
    [JsonPropertyName("eval_duration")]
    public long EvalDuration { get; set; }

    /// <summary>
    /// An encoding of the conversation used in this response, this can be sent in the next request to keep a conversational memory
    /// </summary>
    [JsonPropertyName("")]
    public string? Context { get; set; }

    /// <summary>
    /// Empty if the response was streamed, if not streamed, this will contain the full response
    /// </summary>
    [JsonPropertyName("response")]
    public string? Response { get; set; }
}
