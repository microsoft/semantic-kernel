// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

/// <summary>
/// $$$
/// </summary>
public interface ILocalAgent
{
    /// <summary>
    /// Entry point for calling into an agent with locally managed chat-history.
    /// </summary>
    /// <param name="history">The nexus history at the point the channel is created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchronous enumeration of messages.</returns>
    IAsyncEnumerable<ChatMessageContent> InvokeAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken);
}
