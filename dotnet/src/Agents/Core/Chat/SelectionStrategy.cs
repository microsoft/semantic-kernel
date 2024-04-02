// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Base strategy class for defining completion criteria for a <see cref="AgentChat"/>.
/// </summary>
public abstract class SelectionStrategy
{
    /// <summary>
    /// Implicitly convert a <see cref="SelectionStrategy"/> to a <see cref="SelectionCriteriaCallback"/>.
    /// </summary>
    /// <param name="strategy">A <see cref="ContinuationStrategy"/> instance.</param>
    public static implicit operator SelectionCriteriaCallback(SelectionStrategy strategy)
    {
        return strategy.NextAsync;
    }

    /// <summary>
    /// Evaluate the input message and determine if the nexus has met its completion criteria.
    /// </summary>
    /// <param name="agents">The agents participating in chat.</param>
    /// <param name="history">The most recent message</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True when complete.</returns>
    public abstract Task<Agent> NextAsync(IEnumerable<Agent> agents, IReadOnlyCollection<ChatMessageContent> history, CancellationToken cancellationToken);
}
