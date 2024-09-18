// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Class sponsor that holds extension methods for <see cref="ChatHistory"/> which applied the <see cref="IChatHistoryReducer"/>.
/// </summary>
public static class ChatHistoryReducerExtensions
{
    /// <summary>
    /// Reduces the chat history before sending it to the chat completion provider.
    /// </summary>
    /// <remarks>
    /// If there is no <see cref="IChatHistoryReducer"/> registered in the <see cref="Kernel"/>, the original chat history will be returned.
    /// If the <see cref="IChatHistoryReducer"/> returns null, the original chat history will be returned.
    /// Note: This is not mutating the original chat history.
    /// </remarks>
    /// <param name="chatHistory">The current chat history, including system messages, user messages, assistant messages and tool invocations.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to cancel this operation.</param>
    /// <returns>The reduced chat history if the kernel had one reducer configured, or the same <see cref="ChatHistory"/> if it cannot be reduced.</returns>
    public static async Task<IEnumerable<ChatMessageContent>> ReduceAsync(this ChatHistory chatHistory, Kernel? kernel, CancellationToken cancellationToken)
    {
        if (kernel is null)
        {
            return chatHistory;
        }

        var reducer = kernel.Services.GetService<IChatHistoryReducer>();

        if (reducer is null)
        {
            return chatHistory;
        }

        var reduced = await reducer.ReduceAsync(chatHistory, cancellationToken).ConfigureAwait(false);

        return reduced ?? chatHistory;
    }
}
