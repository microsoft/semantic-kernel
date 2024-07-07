// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines agent execution settings.
/// </summary>
/// <remarks>
/// %%%
/// </remarks>
public sealed class OpenAIAssistantExecutionSettings
{
    /// <summary>
    /// %%%
    /// </summary>
    public int? MaxCompletionTokens { get; init; }

    /// <summary>
    /// %%%
    /// </summary>
    public int? MaxPromptTokens { get; init; }

    /// <summary>
    /// %%%
    /// </summary>
    public bool? ParallelToolCallsEnabled { get; init; }

    //public ToolConstraint? RequiredTool { get; init; } %%% ENUM ???
    //public KernelFunction? RequiredToolFunction { get; init; } %%% PLUGIN ???

    /// <summary>
    /// %%%
    /// </summary>
    public int? TruncationMessageCount { get; init; }
}
