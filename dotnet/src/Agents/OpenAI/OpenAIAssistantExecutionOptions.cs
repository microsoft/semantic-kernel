// Copyright (c) Microsoft. All rights reserved.
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines assistant execution options for each invocation.
/// </summary>
/// <remarks>
/// These options are persisted as a single entry of the assistant's metadata with key: "__run_options"
/// </remarks>
public sealed class OpenAIAssistantExecutionOptions
{
    /// <summary>
    /// Appends additional instructions.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? AdditionalInstructions { get; init; }

    /// <summary>
    /// The maximum number of completion tokens that may be used over the course of the run.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxCompletionTokens { get; init; }

    /// <summary>
    /// The maximum number of prompt tokens that may be used over the course of the run.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxPromptTokens { get; init; }

    /// <summary>
    /// Enables parallel function calling during tool use.  Enabled by default.
    /// Use this property to disable.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ParallelToolCallsEnabled { get; init; }

    /// <summary>
    /// When set, the thread will be truncated to the N most recent messages in the thread.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TruncationMessageCount { get; init; }
}
