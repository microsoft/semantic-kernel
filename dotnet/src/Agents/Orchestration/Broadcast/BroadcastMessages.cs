// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Broadcast;

/// <summary>
/// Common messages used by the <see cref="BroadcastOrchestration{TInput, TOutput}"/>.
/// </summary>
public static class BroadcastMessages
{
    /// <summary>
    /// The input task for a <see cref="BroadcastOrchestration{TInput, TOutput}"/>.
    /// </summary>
    public sealed class Task
    {
        /// <summary>
        /// The input message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = new();
    }

    /// <summary>
    /// A result from a <see cref="BroadcastOrchestration{TInput, TOutput}"/>.
    /// </summary>
    public sealed class Result
    {
        /// <summary>
        /// The result message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = new();
    }

    /// <summary>
    /// Extension method to convert a <see cref="string"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result ToBroadcastResult(this string text, AuthorRole? role = null) => new() { Message = new ChatMessageContent(role ?? AuthorRole.Assistant, text) };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result ToBroadcastResult(this ChatMessageContent message) => new() { Message = message };

    /// <summary>
    /// Extension method to convert a <see cref="string"/> to a <see cref="Task"/>.
    /// </summary>
    public static Task ToBroadcastTask(this string text, AuthorRole? role = null) => new() { Message = new ChatMessageContent(role ?? AuthorRole.User, text) };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Task"/>.
    /// </summary>
    public static Task ToBroadcastTask(this ChatMessageContent message) => new() { Message = message };
}
