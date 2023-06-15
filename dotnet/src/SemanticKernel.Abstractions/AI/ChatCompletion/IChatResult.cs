// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Interface for chat completion results
/// </summary>
public interface IChatResult
{
    /// <summary>
    /// Get the chat message from the result.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Current chat message content</returns>
    Task<ChatMessageBase> GetChatMessageAsync(CancellationToken cancellationToken = default);
}
