﻿// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Defines aggregation behavior for <see cref="AggregatorTerminationStrategy"/>
/// </summary>
public enum AggregateTerminationCondition
{
    /// <summary>
    /// All aggregated strategies must agree on termination.
    /// </summary>
    All,

    /// <summary>
    /// Any single aggregated strategy will terminate.
    /// </summary>
    Any,
}

/// <summary>
/// Aggregate a set of <see cref="TerminationStrategy"/> objects.
/// </summary>
/// <param name="strategies">Set of strategies upon which to aggregate.</param>
public sealed class AggregatorTerminationStrategy(params TerminationStrategy[] strategies) : TerminationStrategy
{
    private readonly TerminationStrategy[] _strategies = strategies;

    /// <summary>
    /// Logical operation for aggregation: All or Any (and/or). Default: All.
    /// </summary>
    public AggregateTerminationCondition Condition { get; init; } = AggregateTerminationCondition.All;

    /// <inheritdoc/>
    protected override async Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        this.Logger.LogAggregatorTerminationStrategyEvaluating(nameof(ShouldAgentTerminateAsync), this._strategies.Length, this.Condition);

        var strategyExecution = this._strategies.Select(s => s.ShouldTerminateAsync(agent, history, cancellationToken));

        var results = await Task.WhenAll(strategyExecution).ConfigureAwait(false);
        bool shouldTerminate =
            this.Condition == AggregateTerminationCondition.All ?
                results.All(r => r) :
                results.Any(r => r);

        return shouldTerminate;
    }
}
