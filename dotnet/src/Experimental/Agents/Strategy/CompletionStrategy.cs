// Copyright (c) Microsoft. All rights reserved.
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

/// <summary>
/// $$$
/// </summary>
public abstract class CompletionStrategy
{
    /// <summary>
    /// $$$$
    /// </summary>
    /// <param name="strategy"></param>
    public static implicit operator CompletionCriteriaCallback(CompletionStrategy strategy)
    {
        return strategy.IsCompleteAsync;
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="message"></param>
    /// <param name="cancellation"></param>
    /// <returns></returns>
    public abstract Task<bool> IsCompleteAsync(ChatMessageContent message, CancellationToken cancellation);
}
