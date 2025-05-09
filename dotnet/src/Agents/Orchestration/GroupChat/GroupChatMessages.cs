// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// Common messages used for agent chat patterns.
/// </summary>
public static class GroupChatMessages
{
    /// <summary>
    /// An empty message instance as a default.
    /// </summary>
    internal static readonly ChatMessageContent Empty = new();

    /// <summary>
    /// Broadcast a message to all <see cref="GroupChatAgentActor"/>.
    /// </summary>
    public sealed class Group
    {
        /// <summary>
        /// The chat message being broadcast.
        /// </summary>
        public IEnumerable<ChatMessageContent> Messages { get; init; } = [];
    }

    /// <summary>
    /// Reset/clear the conversation history for all <see cref="GroupChatAgentActor"/>.
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
    /// Signal a <see cref="GroupChatAgentActor"/> to respond.
    /// </summary>
    public sealed class Speak;

    /// <summary>
    /// The input task.
    /// </summary>
    public sealed class InputTask
    {
        /// <summary>
        /// A task that does not require any action.
        /// </summary>
        public static readonly InputTask None = new();

        /// <summary>
        /// The input that defines the task goal.
        /// </summary>
        public IEnumerable<ChatMessageContent> Messages { get; init; } = [];
    }

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Group"/>.
    /// </summary>
    public static Group AsGroupMessage(this ChatMessageContent message) => new() { Messages = [message] };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Group"/>.
    /// </summary>
    public static Group AsGroupMessage(this IEnumerable<ChatMessageContent> messages) => new() { Messages = messages };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static InputTask AsInputTaskMessage(this IEnumerable<ChatMessageContent> messages) => new() { Messages = messages };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result AsResultMessage(this string text) => new() { Message = new(AuthorRole.Assistant, text) };
}
