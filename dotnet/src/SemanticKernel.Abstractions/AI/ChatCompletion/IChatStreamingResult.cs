// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.AI.ChatCompletion;

/// <summary>
/// Interface for chat completion streaming results
/// </summary>
public interface IChatStreamingResult : IResultBase
{
    /// <summary>
    /// Get the chat message from the streaming result.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Current chat message streaming content</returns>
    IAsyncEnumerable<ChatMessageBase> GetStreamingChatMessageAsync(CancellationToken cancellationToken = default);
}
