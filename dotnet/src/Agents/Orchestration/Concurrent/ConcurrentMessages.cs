// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// Common messages used by the <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
/// </summary>
internal static class ConcurrentMessages
{
    /// <summary>
    /// An empty message instance as a default.
    /// </summary>
    public static readonly ChatMessageContent Empty = new();

    /// <summary>
    /// The input task for a <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
    /// </summary>
    public sealed class Request
    {
        /// <summary>
        /// The request input.
        /// </summary>
        public IList<ChatMessageContent> Messages { get; init; } = [];
    }

    /// <summary>
    /// A result from a <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
    /// </summary>
    public sealed class Result
    {
        /// <summary>
        /// The result message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = Empty;
    }

    /// <summary>
    /// Extension method to convert a <see cref="string"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result AsResultMessage(this string text, AuthorRole? role = null) => new() { Message = new ChatMessageContent(role ?? AuthorRole.Assistant, text) };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result AsResultMessage(this ChatMessageContent message) => new() { Message = message };

    /// <summary>
    /// Extension method to convert a collection of <see cref="ChatMessageContent"/> to a <see cref="ConcurrentMessages.Request"/>.
    /// </summary>
    public static Request AsInputMessage(this IEnumerable<ChatMessageContent> messages) => new() { Messages = [.. messages] };
}
