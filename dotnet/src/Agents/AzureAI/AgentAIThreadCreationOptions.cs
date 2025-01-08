// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using AzureAIP = Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Thread creation options.
/// </summary>
public sealed class AzureAIThreadCreationOptions
{
    /// <summary>
    /// Optional messages to initialize thread with...
    /// </summary>
    /// <remarks>
    /// Only supports messages with role = User or Assistant
    /// </remarks>
    public IReadOnlyList<ChatMessageContent>? Messages { get; init; }

    /// <summary>
    /// A set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </summary>
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }

    /// <summary>
    /// Optional file-ids made available to the code_interpreter tool, if enabled.
    /// </summary>
    public AzureAIP.ToolResources? ToolResources { get; init; }
}
