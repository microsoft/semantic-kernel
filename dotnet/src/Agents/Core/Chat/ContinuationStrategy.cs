// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Base strategy class for defining completion criteria for a <see cref="AgentChat"/>.
/// </summary>
public abstract class ContinuationStrategy
{
    /// <summary>
    /// Implicitly convert a <see cref="ContinuationStrategy"/> to a <see cref="ContinuationCriteriaCallback"/>.
    /// </summary>
    /// <param name="strategy">A <see cref="ContinuationStrategy"/> instance.</param>
    public static implicit operator ContinuationCriteriaCallback(ContinuationStrategy strategy)
    {
        return strategy.ShouldContinue;
    }

    /// <summary>
    /// Evaluate the input message and determine if the nexus has met its completion criteria.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="history">The most recent message</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True when complete.</returns>
    public abstract Task<bool> ShouldContinue(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default);
}
