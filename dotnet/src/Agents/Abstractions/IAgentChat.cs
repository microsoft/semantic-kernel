// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Point of interaction Interface for one or more agents.
/// </summary>
public interface IAgentChat
{
    /// <summary>
    /// Indicates if the chat is active.
    /// </summary>
    bool IsActive { get; }

    /// <summary>
    /// Factory for creating loggers.
    /// </summary>
    ILoggerFactory LoggerFactory { get; init; }

    /// <summary>
    /// Adds a chat message to the chat history.
    /// </summary>
    /// <param name="message">The chat message to add.</param>
    void AddChatMessage(ChatMessageContent message);

    /// <summary>
    /// Adds multiple chat messages to the chat history.
    /// </summary>
    /// <param name="messages">The chat messages to add.</param>
    void AddChatMessages(IReadOnlyList<ChatMessageContent> messages);

    /// <summary>
    /// Retrieves the chat messages asynchronously.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of chat messages.</returns>
    IAsyncEnumerable<ChatMessageContent> GetChatMessagesAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Retrieves the chat messages for a specific agent asynchronously.
    /// </summary>
    /// <param name="agent">The agent whose chat messages to retrieve.</param>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of chat messages.</returns>
    IAsyncEnumerable<ChatMessageContent> GetChatMessagesAsync(Agent? agent, [EnumeratorCancellation] CancellationToken cancellationToken = default);

    /// <summary>
    /// Invokes the chat asynchronously.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of chat messages.</returns>
    IAsyncEnumerable<ChatMessageContent> InvokeAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Invokes the chat with streaming messages asynchronously.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An asynchronous enumeration of streaming chat messages.</returns>
    IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(CancellationToken cancellationToken = default);

    /// <summary>
    /// Resets the chat asynchronously.
    /// </summary>
    /// <param name="cancellationToken">The cancellation token to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A task representing the asynchronous operation.</returns>
    Task ResetAsync(CancellationToken cancellationToken = default);
}
