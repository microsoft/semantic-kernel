// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Thread creation settings.
/// </summary>
public sealed class OpenAIThreadCreationSettings
{
    /// <summary>
    /// Optional file-ids made available to the code_interpreter tool, if enabled.
    /// </summary>
    public IReadOnlyList<string>? CodeInterpterFileIds { get; init; }

    /// <summary>
    /// Set if code-interpreter is enabled.
    /// </summary>
    public bool EnableCodeInterpreter { get; init; }

    /// <summary>
    /// Optional messages to initialize thread with..
    /// </summary>
    public IReadOnlyList<ChatMessageContent>? Messages { get; init; }

    /// <summary>
    /// Enables file-serach if specified.
    /// </summary>
    public string? VectorStoreId { get; init; }

    /// <summary>
    /// A set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </summary>
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }
}
