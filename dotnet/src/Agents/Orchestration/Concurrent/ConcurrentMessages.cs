// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Concurrent;

/// <summary>
/// Common messages used by the <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
/// </summary>
public static class ConcurrentMessages
{
    /// <summary>
    /// The input task for a <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
    /// </summary>
    public sealed class Request
    {
        /// <summary>
        /// The request message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = new();
    }

    /// <summary>
    /// A result from a <see cref="ConcurrentOrchestration{TInput, TOutput}"/>.
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
    public static Result ToResult(this string text, AuthorRole? role = null) => new() { Message = new ChatMessageContent(role ?? AuthorRole.Assistant, text) };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result ToResult(this ChatMessageContent message) => new() { Message = message };

    /// <summary>
    /// Extension method to convert a <see cref="string"/> to a <see cref="Request"/>.
    /// </summary>
    public static Request ToRequest(this string text, AuthorRole? role = null) => new() { Message = new ChatMessageContent(role ?? AuthorRole.User, text) };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Request"/>.
    /// </summary>
    public static Request ToInput(this ChatMessageContent message) => new() { Message = message };
}
