// Copyright (c) Microsoft. All rights reserved.

using System.Collections.ObjectModel;

namespace Microsoft.SemanticKernel.Experimental.Assistants;

/// <summary>
/// Represents a message that is part of an assistant thread.
/// </summary>
public interface IChatMessage
{
    /// <summary>
    /// The message identifier (which can be referenced in API endpoints).
    /// </summary>
    string Id { get; }

    /// <summary>
    /// The id of the assistant associated with the a message where role = "assistant", otherwise null.
    /// </summary>
    string? AssistantId { get; }

    /// <summary>
    /// The chat message content.
    /// </summary>
    string Content { get; }

    /// <summary>
    /// The role associated with the chat message.
    /// </summary>
    string Role { get; }

    /// <summary>
    /// Properties associated with the message.
    /// </summary>
    ReadOnlyDictionary<string, object> Properties { get; }
}
