// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Base strategy class for defining termination criteria for a <see cref="AgentChat"/>.
/// </summary>
public abstract class TerminationStrategy
{
    /// <summary>
    /// Implicitly convert a <see cref="TerminationStrategy"/> to a <see cref="TerminationCriteriaCallback"/>.
    /// </summary>
    /// <param name="strategy">A <see cref="TerminationStrategy"/> instance.</param>
    public static implicit operator TerminationCriteriaCallback(TerminationStrategy strategy)
    {
        return strategy.ShouldContinue;
    }

    /// <summary>
    /// Evaluate the input message and determine if the nexus has met its completion criteria.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="history">The most recent message</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>True to terminate chat loop.</returns>
    public abstract Task<bool> ShouldContinue(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default);
}
