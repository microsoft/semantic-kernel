// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Orchestration.GroupChat;

/// <summary>
/// Common messages used for agent chat patterns.
/// </summary>
public static class ChatMessages
{
    /// <summary>
    /// An empty message instance as a default.
    /// </summary>
    internal static readonly ChatMessageContent Empty = new();

    /// <summary>
    /// Broadcast a message to all <see cref="ChatAgentActor"/>.
    /// </summary>
    public sealed class Group
    {
        /// <summary>
        /// The chat message being broadcast.
        /// </summary>
        public ChatMessageContent Message { get; init; } = Empty;
    }

    /// <summary>
    /// Reset/clear the conversation history for all <see cref="ChatAgentActor"/>.
    /// </summary>
    public sealed class Reset { }

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
    /// Signal a <see cref="ChatAgentActor"/> to respond.
    /// </summary>
    public sealed class Speak { }

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
        public ChatMessageContent Message { get; init; } = Empty;
    }

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Group"/>.
    /// </summary>
    public static Group ToGroup(this ChatMessageContent message) => new() { Message = message };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result ToResult(this ChatMessageContent message) => new() { Message = message };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static InputTask ToInputTask(this ChatMessageContent message) => new() { Message = message };
}
