// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// $$$
/// </summary>
public enum AggregateTerminationCondition
{
    /// <summary>
    /// $$$
    /// </summary>
    All,

    /// <summary>
    /// $$$
    /// </summary>
    Any,
}

/// <summary>
/// $$$
/// </summary>
public sealed class AggregateTerminationStrategy : AgentBoundTerminationStrategy
{
    private readonly TerminationStrategy[] _strategies;

    /// <summary>
    /// $$$
    /// </summary>
    public AggregateTerminationCondition Condition { get; set; } = AggregateTerminationCondition.All;

    /// <inheritdoc/>
    protected override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        var strategyExecution = this._strategies.Select(s => s.ShouldTerminateAsync(agent, history, cancellationToken));

        var results = await Task.WhenAll(strategyExecution).ConfigureAwait(false);
        bool shouldTerminate =
            this.Condition == AggregateTerminationCondition.All ?
                results.All(r => r) :
                results.Any(r => r);

        return shouldTerminate;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="AggregateTerminationStrategy"/> class.
    /// </summary>
    /// <param name="strategies">$$$</param>
    public AggregateTerminationStrategy(params TerminationStrategy[] strategies)
    {
        this._strategies = strategies;
    }
}
