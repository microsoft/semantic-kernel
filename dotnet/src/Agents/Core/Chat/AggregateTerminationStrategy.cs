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
public sealed class AggregateTerminationStrategy : TerminationStrategy
{
    private readonly Agent? _agent;
    private readonly TerminationStrategy[] _strategies; // $$$ ANY / ALL

    /// <summary>
    /// $$$
    /// </summary>
    public AggregateTerminationCondition Condition { get; } = AggregateTerminationCondition.All;

    /// <inheritdoc/>
    public override async Task<bool> ShouldTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Agent must match, if specified.
        if (this._agent != null && this._agent.Id != agent.Id)
        {
            return false;
        }

        // Most recent message
        var message = history[history.Count - 1];

        var strategyExecution = this._strategies.Select(s => s.ShouldTerminateAsync(agent, history, cancellationToken));

        bool shouldTerminate = false;

        if (this.Condition == AggregateTerminationCondition.All)
        {
            var results = await Task.WhenAll(strategyExecution).ConfigureAwait(false);
            shouldTerminate = results.All(r => r);
        }
        else
        {
            Task<bool> anyTask = await Task.WhenAny(strategyExecution).ConfigureAwait(false);
            shouldTerminate = await anyTask.ConfigureAwait(false);
        }

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

    /// <summary>
    /// Initializes a new instance of the <see cref="AggregateTerminationStrategy"/> class.
    /// </summary>
    /// <param name="agent">The agent targeted by this strategy</param>
    /// <param name="strategies">$$$</param>
    public AggregateTerminationStrategy(Agent agent, params TerminationStrategy[] strategies)
    {
        this._agent = agent;
        this._strategies = strategies;
    }
}
