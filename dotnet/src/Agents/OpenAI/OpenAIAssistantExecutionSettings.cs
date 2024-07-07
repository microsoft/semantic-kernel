// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines agent execution settings for each invocation.
/// </summary>
/// <remarks>
/// These settings are persisted as a single entry of the agent's metadata with key: "__settings"
/// </remarks>
public sealed class OpenAIAssistantExecutionSettings
{
    /// <summary>
    /// The maximum number of completion tokens that may be used over the course of the run.
    /// </summary>
    public int? MaxCompletionTokens { get; init; }

    /// <summary>
    /// The maximum number of prompt tokens that may be used over the course of the run.
    /// </summary>
    public int? MaxPromptTokens { get; init; }

    /// <summary>
    /// Enables parallel function calling during tool use.  Enabled by default.
    /// Use this property to disable.
    /// </summary>
    public bool? ParallelToolCallsEnabled { get; init; }

    //public ToolConstraint? RequiredTool { get; init; } // %%% ENUM ???
    //public KernelFunction? RequiredToolFunction { get; init; } // %%% PLUGIN ???

    /// <summary>
    /// When set, the thread will be truncated to the N most recent messages in the thread.
    /// </summary>
    public int? TruncationMessageCount { get; init; }
}
