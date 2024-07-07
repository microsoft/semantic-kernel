// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines per invocation execution settings that override the assistant's default settings.
/// </summary>
/// <remarks>
/// Not applicable to <see cref="AgentChat"/> usage.
/// </remarks>
public sealed class OpenAIAssistantInvocationSettings
{
    /// <summary>
    /// Override the AI model targeted by the agent.
    /// </summary>
    public string? ModelName { get; init; }

    /// <summary>
    /// Set if code_interpreter tool is enabled.
    /// </summary>
    public bool EnableCodeInterpreter { get; init; }

    /// <summary>
    /// Set if file_search tool is enabled.
    /// </summary>
    public bool EnableFileSearch { get; init; }

    /// <summary>
    /// Set if json response-format is enabled.
    /// </summary>
    public bool? EnableJsonResponse { get; init; }

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

    /// <summary>
    /// The sampling temperature to use, between 0 and 2.
    /// </summary>
    public float? Temperature { get; init; }

    /// <summary>
    /// An alternative to sampling with temperature, called nucleus sampling, where the model
    /// considers the results of the tokens with top_p probability mass.
    /// So 0.1 means only the tokens comprising the top 10% probability mass are considered.
    /// </summary>
    /// <remarks>
    /// Recommended to set this or temperature but not both.
    /// </remarks>
    public float? TopP { get; init; }

    /// <summary>
    /// A set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </summary>
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }
}
