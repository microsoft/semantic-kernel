// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Sequential;

/// <summary>
/// A message that describes the input task and captures results for a <see cref="SequentialOrchestration{TInput,TOutput}"/>.
/// </summary>
internal static class SequentialMessages
{
    /// <summary>
    /// An empty message instance as a default.
    /// </summary>
    public static readonly ChatMessageContent Empty = new();

    /// <summary>
    /// Represents a request containing a sequence of chat messages to be processed by the sequential orchestration.
    /// </summary>
    public sealed class Request
    {
        /// <summary>
        /// The request input.
        /// </summary>
        public IList<ChatMessageContent> Messages { get; init; } = [];
    }

    /// <summary>
    /// Represents a response containing the result message from the sequential orchestration.
    /// </summary>
    public sealed class Response
    {
        /// <summary>
        /// The response message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = Empty;
    }

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="SequentialMessages.Request"/>.
    /// </summary>
    /// <param name="message">The chat message to include in the request.</param>
    /// <returns>A <see cref="SequentialMessages.Request"/> containing the provided messages.</returns>
    public static Request AsRequestMessage(this ChatMessageContent message) => new() { Messages = [message] };

    /// <summary>
    /// Extension method to convert a collection of <see cref="ChatMessageContent"/> to a <see cref="SequentialMessages.Request"/>.
    /// </summary>
    /// <param name="messages">The collection of chat messages to include in the request.</param>
    /// <returns>A <see cref="SequentialMessages.Request"/> containing the provided messages.</returns>
    public static Request AsRequestMessage(this IEnumerable<ChatMessageContent> messages) => new() { Messages = [.. messages] };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="SequentialMessages.Response"/>.
    /// </summary>
    /// <param name="message">The chat message to include in the response.</param>
    /// <returns>A <see cref="SequentialMessages.Response"/> containing the provided message.</returns>
    public static Response AsResponseMessage(this ChatMessageContent message) => new() { Message = message };
}
