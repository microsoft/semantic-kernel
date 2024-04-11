// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Base strategy class for selecting the next agent for a <see cref="AgentGroupChat"/>.
/// </summary>
public abstract class SelectionStrategy
{
    /// <summary>
    /// Determine which agent goes next.
    /// </summary>
    /// <param name="agents">The agents participating in chat.</param>
    /// <param name="history">The chat history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The agent who shall take the next turn.</returns>
    public abstract Task<Agent> NextAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default);
}
