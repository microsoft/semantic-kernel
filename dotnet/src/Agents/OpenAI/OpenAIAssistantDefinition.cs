// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// The data associated with an assistant's definition.
/// </summary>
public sealed class OpenAIAssistantDefinition
{
    /// <summary>
    /// The ID of the model to use.
    /// </summary>
    public string? Model { get; init; }

    /// <summary>
    /// The description of the assistant.
    /// </summary>
    public string? Description { get; init; }

    /// <summary>
    /// The assistant's unique id.  (Ignored on create.)
    /// </summary>
    public string? Id { get; init; }

    /// <summary>
    /// The system instructions for the assistant to use.
    /// </summary>
    public string? Instructions { get; init; }

    /// <summary>
    /// The name of the assistant.
    /// </summary>
    public string? Name { get; init; }

    /// <summary>
    /// Set if code-interpreter is enabled.
    /// </summary>
    public bool EnableCodeInterpreter { get; init; }

    /// <summary>
    /// Set if retrieval is enabled.
    /// </summary>
    public bool EnableRetrieval { get; init; }

    /// <summary>
    /// A list of previously uploaded file IDs to attach to the assistant.
    /// </summary>
    public IEnumerable<string>? FileIds { get; init; }

    /// <summary>
    /// A set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </summary>
    public IReadOnlyDictionary<string, string>? Metadata { get; init; }
}
