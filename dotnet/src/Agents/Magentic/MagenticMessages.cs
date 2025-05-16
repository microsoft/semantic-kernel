// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Magentic;

/// <summary>
/// Common messages used for agent chat patterns.
/// </summary>
public static class MagenticMessages
{
    /// <summary>
    /// An empty message instance as a default.
    /// </summary>
    internal static readonly ChatMessageContent Empty = new();

    /// <summary>
    /// Broadcast a message to all <see cref="MagenticAgentActor"/>.
    /// </summary>
    public sealed class Group
    {
        /// <summary>
        /// The chat message being broadcast.
        /// </summary>
        public IEnumerable<ChatMessageContent> Messages { get; init; } = [];
    }

    /// <summary>
    /// Reset/clear the conversation history for all <see cref="MagenticAgentActor"/>.
    /// </summary>
    public sealed class Reset;

    /// <summary>
    /// The final result.
    /// </summary>
    public sealed class Result
    {
        /// <summary>
        /// The chat response message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = Empty;
    }

    /// <summary>
    /// Signal a <see cref="MagenticAgentActor"/> to respond.
    /// </summary>
    public sealed class Speak;

    /// <summary>
    /// The input task.
    /// </summary>
    public sealed class InputTask
    {
        /// <summary>
        /// The input that defines the task goal.
        /// </summary>
        public IEnumerable<ChatMessageContent> Messages { get; init; } = [];
    }

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Group"/> message.
    /// </summary>
    public static Group AsGroupMessage(this ChatMessageContent message) => new() { Messages = [message] };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Group"/> message.
    /// </summary>
    public static Group AsGroupMessage(this IEnumerable<ChatMessageContent> messages) => new() { Messages = messages };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/> message.
    /// </summary>
    public static InputTask AsInputTaskMessage(this IEnumerable<ChatMessageContent> messages) => new() { Messages = messages };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/> message.
    /// </summary>
    public static Result AsResultMessage(this ChatMessageContent message) => new() { Message = message };
}
