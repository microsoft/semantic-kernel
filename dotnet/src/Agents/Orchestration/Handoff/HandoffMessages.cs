// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.Orchestration.Handoff;

/// <summary>
/// A message that describes the input task and captures results for a <see cref="HandoffOrchestration{TInput,TOutput}"/>.
/// </summary>
internal static class HandoffMessages
{
    /// <summary>
    /// An empty message instance as a default.
    /// </summary>
    internal static readonly ChatMessageContent Empty = new();

    /// <summary>
    /// The input message.
    /// </summary>
    public sealed class InputTask
    {
        /// <summary>
        /// The orchestration input messages.
        /// </summary>
        public IList<ChatMessageContent> Messages { get; init; } = [];
    }

    /// <summary>
    /// The final result.
    /// </summary>
    public sealed class Result
    {
        /// <summary>
        /// The orchestration result message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = Empty;
    }

    /// <summary>
    /// Signals the handoff to another agent.
    /// </summary>
    public sealed class Request;

    /// <summary>
    /// Broadcast an agent response to all actors in the orchestration.
    /// </summary>
    public sealed class Response
    {
        /// <summary>
        /// The chat response message.
        /// </summary>
        public ChatMessageContent Message { get; init; } = Empty;
    }

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static InputTask AsInputTaskMessage(this IEnumerable<ChatMessageContent> messages) => new() { Messages = [.. messages] };

    /// <summary>
    /// Extension method to convert a <see cref="ChatMessageContent"/> to a <see cref="Result"/>.
    /// </summary>
    public static Result AsResultMessage(this ChatMessageContent message) => new() { Message = message };
}
