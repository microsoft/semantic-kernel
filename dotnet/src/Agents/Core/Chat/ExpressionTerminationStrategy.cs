// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Signals termination when the most recent message matches against the defined regular expressions
/// for the specified agent (if provided).
/// </summary>
public sealed class ExpressionTerminationStrategy : AgentBoundTerminationStrategy
{
    private readonly string[] _expressions;

    /// <inheritdoc/>
    protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Most recent message
        var message = history[history.Count - 1];

        // Evaluate expressions for match
        foreach (var expression in this._expressions)
        {
            if (Regex.IsMatch(message.Content, expression))
            {
                return Task.FromResult(true);
            }
        }

        return Task.FromResult(false);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="ExpressionTerminationStrategy"/> class.
    /// </summary>
    /// <param name="expressions">A list of regular expressions, that if</param>
    public ExpressionTerminationStrategy(params string[] expressions)
    {
        this._expressions = expressions;
    }
}
