// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Settings that affect behavior of <see cref="AgentGroupChat"/>.
/// </summary>
/// <remarks>
/// Default behavior result in no agent selection.
/// </remarks>
public class AgentGroupChatSettings
{
    /// <summary>
    /// Strategy for selecting the next agent.  Dfeault strategy limited to a single iteration and no termination criteria.
    /// </summary>
    /// <remarks>
    /// See <see cref="TerminationStrategy"/>.
    /// </remarks>
    public TerminationStrategy TerminationStrategy { get; init; } = new DefaultTerminationStrategy();

    /// <summary>
    /// Strategy for selecting the next agent.  Defaults to <see cref="SequentialSelectionStrategy"/>.
    /// </summary>
    /// <remarks>
    /// See <see cref="SelectionStrategy"/>.
    /// </remarks>
    public SelectionStrategy SelectionStrategy { get; init; } = new SequentialSelectionStrategy();

    /// <summary>
    /// The termination strategy attached to the default state of <see cref="AgentGroupChatSettings.TerminationStrategy"/>.
    /// This strategy will execute without signaling termination.  Execution of <see cref="AgentGroupChat"/> will only be
    /// bound by <see cref="TerminationStrategy.MaximumIterations"/>.
    /// </summary>
    internal sealed class DefaultTerminationStrategy : TerminationStrategy
    {
        /// <inheritdoc/>
        protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
        {
            return Task.FromResult(false);
        }

        public DefaultTerminationStrategy()
        {
            this.MaximumIterations = 1;
        }
    }
}
