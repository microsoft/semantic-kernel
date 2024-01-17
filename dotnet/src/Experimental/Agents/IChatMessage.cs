// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Collections.ObjectModel;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Represents a message that is part of an agent thread.
/// </summary>
public interface IChatMessage
{
    /// <summary>
    /// The message identifier (which can be referenced in API endpoints).
    /// </summary>
    string Id { get; }

    /// <summary>
    /// The id of the agent associated with the a message where role = "agent", otherwise null.
    /// </summary>
    string? AgentId { get; }

    /// <summary>
    /// The chat message content.
    /// </summary>
    string Content { get; }

    /// <summary>
    /// The role associated with the chat message.
    /// </summary>
    string Role { get; }

    /// <summary>
    /// Annotations associated with the message.
    /// </summary>
    IList<IAnnotation> Annotations { get; }

    /// <summary>
    /// Properties associated with the message.
    /// </summary>
    ReadOnlyDictionary<string, object> Properties { get; }

    /// <summary>
    /// Defines message annotation.
    /// </summary>
    interface IAnnotation
    {
        /// <summary>
        /// The file identifier.
        /// </summary>
        string FileId { get; }

        /// <summary>
        /// The text in the message content that needs to be replaced.
        /// </summary>
        string Label { get; }

        /// <summary>
        /// The citation.
        /// </summary>
        string? Quote { get; }

        /// <summary>
        /// Start index of the citation.
        /// </summary>
        int StartIndex { get; }

        /// <summary>
        /// End index of the citation.
        /// </summary>
        int EndIndex { get; }
    }
}
