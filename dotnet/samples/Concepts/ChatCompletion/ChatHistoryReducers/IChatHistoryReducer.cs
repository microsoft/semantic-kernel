// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;

namespace ChatCompletion;

/// <summary>
/// Interface for reducing the chat history before sending it to the chat completion provider.
/// </summary>
public interface IChatHistoryReducer
{
    /// <summary>
    /// Reduce the <see cref="ChatHistory"/> before sending it to the <see cref="IChatCompletionService"/>.
    /// </summary>
    /// <param name="chatHistory">Instance of <see cref="ChatHistory"/>to be reduced.</param>
    /// <param name="cancellationToken">Cancellation token.</param>
    /// <returns>An optional <see cref="IEnumerable{ChatMessageContent}"/> which contains the reduced chat messages or null if chat history can be used as is.</returns>
    Task<IEnumerable<ChatMessageContent>?> ReduceAsync(ChatHistory chatHistory, CancellationToken cancellationToken);
}
