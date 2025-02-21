// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines assistant execution options for each invocation.
/// </summary>
/// <remarks>
/// These options are persisted as a single entry of the assistant's metadata with key: "__run_options".
/// </remarks>
[Experimental("SKEXP0110")]
[Obsolete("Use RunCreationOptions to specify assistant invocation behavior.")]
public sealed class OpenAIAssistantExecutionOptions
{
    /// <summary>
    /// Gets the additional instructions.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public string? AdditionalInstructions { get; init; }

    /// <summary>
    /// Gets the maximum number of completion tokens that can be used over the course of the run.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxCompletionTokens { get; init; }

    /// <summary>
    /// Gets the maximum number of prompt tokens that can be used over the course of the run.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? MaxPromptTokens { get; init; }

    /// <summary>
    /// Gets a value that indicates whether parallel function calling is enabled during tool use.
    /// </summary>
    /// <value>
    /// <see langword="true"/> if parallel function calling is enabled during tool use; otherwise, <see langword="false"/>. The default is <see langword="true"/>.
    /// </value>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public bool? ParallelToolCallsEnabled { get; init; }

    /// <summary>
    /// Gets the number of recent messages that the thread will be truncated to.
    /// </summary>
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public int? TruncationMessageCount { get; init; }
}
