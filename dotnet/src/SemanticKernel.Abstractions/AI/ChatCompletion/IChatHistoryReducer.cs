// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.ChatCompletion;

/// <summary>
/// Interface for reducing the chat history before sending it to the chat completion provider.
/// </summary>
/// <remarks>
/// This interface can be implemented in order to apply custom logic for prompt truncation during inference.
/// </remarks>
public interface IChatHistoryReducer
{
    /// <summary>
    /// Reduces the chat history to a smaller size before sending it to the chat completion provider.
    /// </summary>
    /// <param name="chatHistory">The current chat history, including system messages, user messages, assistant messages and tool invocations.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests.</param>
    /// <returns>The reduced history, or 'null' if no reduction has occurred.</returns>
    Task<IEnumerable<ChatMessageContent>?> ReduceAsync(IReadOnlyList<ChatMessageContent> chatHistory, CancellationToken cancellationToken);
}
