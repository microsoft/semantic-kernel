// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Contract for an agent that utilizes a <see cref="ChatHistoryChannel"/>.
/// </summary>
public interface IChatHistoryHandler
{
    /// <summary>
    /// Entry point for calling into an agent from a a <see cref="ChatHistoryChannel"/>.
    /// </summary>
    /// <param name="history">The chat history at the point the channel is created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        IReadOnlyList<ChatMessageContent> history,
        CancellationToken cancellationToken = default);
}
