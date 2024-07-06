// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines agent execution settings.
/// </summary>
public class OpenAIAssistantExecutionSettings
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

    //ToolConstraint // %%%

    /// <summary>
    /// %%%
    /// </summary>
    public int? TruncationMessageCount { get; init; }
}
