// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Provides settings that affect the behavior of <see cref="AgentGroupChat"/> instances.
/// </summary>
/// <remarks>
/// The default behavior results in no agent selection.
/// </remarks>
[Experimental("SKEXP0110")]
public class AgentGroupChatSettings
{
    /// <summary>
    /// Gets the strategy for terminating the agent.
    /// </summary>
    /// <value>
    /// The strategy for terminating the agent. The default strategy a single iteration and no termination criteria.
    /// </value>
    /// <seealso cref="SelectionStrategy"/>
    public TerminationStrategy TerminationStrategy { get; init; } = new DefaultTerminationStrategy();

    /// <summary>
    /// Gets the strategy for selecting the next agent.
    /// </summary>
    /// <value>
    /// The strategy for selecting the next agent. The default is <see cref="SequentialSelectionStrategy"/>.
    /// </value>
    /// <seealso cref="TerminationStrategy"/>
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
