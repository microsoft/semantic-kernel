// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using Microsoft.SemanticKernel.Agents.History;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Contract for an agent that utilizes a <see cref="ChatHistoryChannel"/>.
/// </summary>
public interface IChatHistoryHandler
{
    /// <summary>
    /// An optional history reducer to apply to the chat history prior processing.
    /// </summary>
    IChatHistoryReducer? HistoryReducer { get; init; }

    /// <summary>
    /// Entry point for calling into an agent from a <see cref="ChatHistoryChannel"/>.
    /// </summary>
    /// <param name="history">The chat history at the point the channel is created.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);

    /// <summary>
    /// Entry point for calling into an agent from a <see cref="ChatHistoryChannel"/> for streaming content.
    /// </summary>
    /// <param name="history">The chat history at the point the channel is created.</param>
    /// <param name="arguments">Optional arguments to pass to the agents's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="kernel">Optional <see cref="Kernel"/> override containing services, plugins, and other state for use by the agent.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of streaming content.</returns>
    IAsyncEnumerable<StreamingChatMessageContent> InvokeStreamingAsync(
        ChatHistory history,
        KernelArguments? arguments = null,
        Kernel? kernel = null,
        CancellationToken cancellationToken = default);
}
