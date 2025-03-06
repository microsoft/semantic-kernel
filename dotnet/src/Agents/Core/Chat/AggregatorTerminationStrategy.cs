// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Defines aggregation behavior for <see cref="AggregatorTerminationStrategy"/>.
/// </summary>
[Experimental("SKEXP0110")]
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
/// Provides methods to aggregate a set of <see cref="TerminationStrategy"/> objects.
/// </summary>
/// <param name="strategies">The set of strategies upon which to aggregate.</param>
[Experimental("SKEXP0110")]
public sealed class AggregatorTerminationStrategy(params TerminationStrategy[] strategies) : TerminationStrategy
{
    private readonly TerminationStrategy[] _strategies = strategies;

    /// <summary>
    /// Gets the logical operation for aggregation.
    /// </summary>
    /// <value>
    /// The logical operation for aggregation, which can be <see cref="AggregateTerminationCondition.All"/> or <see cref="AggregateTerminationCondition.Any"/>. The default is <see cref="AggregateTerminationCondition.All"/>.
    /// </value>
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
