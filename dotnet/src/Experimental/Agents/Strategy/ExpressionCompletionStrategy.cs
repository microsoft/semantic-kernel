// Copyright (c) Microsoft. All rights reserved.
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

/// <summary>
/// $$$
/// </summary>
public sealed class ExpressionCompletionStrategy : CompletionStrategy
{
    private readonly string[] _expressions;

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="expressions"></param>
    public ExpressionCompletionStrategy(params string[] expressions)
    {
        this._expressions = expressions;
    }

    /// <inheritdoc/>
    public override Task<bool> IsCompleteAsync(ChatMessageContent message, CancellationToken cancellation)
    {
        foreach (var expression in this._expressions)
        {
            if (Regex.IsMatch(message.Content, expression)) // $$$ PERF ???
            {
                return Task.FromResult(true);
            }
        }

        return Task.FromResult(false);
    }
}
