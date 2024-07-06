// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Defines per invocation execution settings.
/// </summary>
public sealed class OpenAIAssistantInvocationSettings : OpenAIAssistantExecutionSettings
{
    /// <summary>
    /// Identifies the AI model targeted by the agent.
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
    /// %%%
    /// </summary>
    public float? Temperature { get; init; }

    /// <summary>
    /// %%%
    /// </summary>
    public float? TopP { get; init; }

    /// <summary>
    /// A set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </summary>
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }
}
