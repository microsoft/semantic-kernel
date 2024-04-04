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
public sealed class ExpressionTerminationStrategy : TerminationStrategy
{
    private readonly Agent? _agent;
    private readonly string[] _expressions;

    /// <inheritdoc/>
    public override Task<bool> ShouldTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Agent must match, if specified.
        if (this._agent != null && this._agent.Id != agent.Id)
        {
            return Task.FromResult(false);
        }

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

    /// <summary>
    /// Initializes a new instance of the <see cref="ExpressionTerminationStrategy"/> class.
    /// </summary>
    /// <param name="agent">The agent targeted by this strategy</param>
    /// <param name="expressions">The regular expression to match against message content</param>
    public ExpressionTerminationStrategy(Agent agent, params string[] expressions)
    {
        this._agent = agent;
        this._expressions = expressions;
    }
}
