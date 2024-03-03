// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// Completion strategy based on the evaluation of a set regular expressions.
/// </summary>
public sealed class ExpressionCompletionStrategy : CompletionStrategy
{
    private readonly string[] _expressions;

    /// <summary>
    /// Initializes a new instance of the <see cref="SemanticCompletionStrategy"/> class.
    /// </summary>
    /// <param name="expressions"></param>
    public ExpressionCompletionStrategy(params string[] expressions)
    {
        this._expressions = expressions;
    }

    /// <inheritdoc/>
    public override Task<bool> IsCompleteAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken)
    {
        var message = history.Last();

        foreach (var expression in this._expressions)
        {
            if (Regex.IsMatch(message.Content, expression))
            {
                return Task.FromResult(true);
            }
        }

        return Task.FromResult(false);
    }
}
