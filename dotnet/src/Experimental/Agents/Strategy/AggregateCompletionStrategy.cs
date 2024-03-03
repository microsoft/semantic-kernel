// Copyright (c) Microsoft. All rights reserved.
using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

/// <summary>
/// $$$
/// </summary>
public sealed class AggregateCompletionStrategy : CompletionStrategy, IEnumerable<CompletionStrategy>
{
    private readonly CompletionStrategy[] _strategies;

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="strategies"></param>
    public AggregateCompletionStrategy(params CompletionStrategy[] strategies)
    {
        this._strategies = strategies;
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="strategies"></param>
    public AggregateCompletionStrategy(IEnumerable<CompletionStrategy> strategies)
    {
        this._strategies = strategies.ToArray();
    }

    /// <inheritdoc/>
    public override async Task<bool> IsCompleteAsync(ChatMessageContent message, CancellationToken cancellation)
    {
        var result = await Task.WhenAll(this._strategies.Select(s => s.IsCompleteAsync(message, cancellation))).ConfigureAwait(false);

        return result.All(r => r);
    }

    IEnumerator<CompletionStrategy> IEnumerable<CompletionStrategy>.GetEnumerator()
    {
        return ((IEnumerable<CompletionStrategy>)this._strategies).GetEnumerator();
    }

    IEnumerator IEnumerable.GetEnumerator()
    {
        return this._strategies.GetEnumerator();
    }
}
