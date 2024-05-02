// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Signals termination when the most recent message matches against the defined regular expressions
/// for the specified agent (if provided).
/// </summary>
public sealed class RegexTerminationStrategy : TerminationStrategy
{
    private readonly Regex[] _expressions;

    /// <summary>
    /// Initializes a new instance of the <see cref="RegexTerminationStrategy"/> class.
    /// </summary>
    /// <param name="expressions">
    /// A list of regular expressions to match against an agent's last message to
    /// determine whether processing should terminate.
    /// </param>
    public RegexTerminationStrategy(params string[] expressions)
    {
        Verify.NotNull(expressions);

        this._expressions = expressions
            .Where(s => s is not null)
            .Select(e => new Regex(e, RegexOptions.Compiled))
            .ToArray();
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="RegexTerminationStrategy"/> class.
    /// </summary>
    /// <param name="expressions">
    /// A list of regular expressions to match against an agent's last message to
    /// determine whether processing should terminate.
    /// </param>
    public RegexTerminationStrategy(params Regex[] expressions)
    {
        Verify.NotNull(expressions);

        this._expressions = expressions.OfType<Regex>().ToArray();
    }

    /// <inheritdoc/>
    protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Most recent message
        var message = history[history.Count - 1].Content;

        if (this.Logger.IsEnabled(LogLevel.Debug)) // Avoid boxing if not enabled
        {
            this.Logger.LogDebug("[{MethodName}] Evaluating expressions: {ExpressionCount}", nameof(ShouldAgentTerminateAsync), this._expressions.Length);
        }

        // Evaluate expressions for match
        foreach (var expression in this._expressions)
        {
            this.Logger.LogDebug("[{MethodName}] Evaluating expression: {Expression}", nameof(ShouldAgentTerminateAsync), expression);

            if (expression.IsMatch(message))
            {
                this.Logger.LogInformation("[{MethodName}] Expression matched: {Expression}", nameof(ShouldAgentTerminateAsync), expression);

                return Task.FromResult(true);
            }
        }

        this.Logger.LogInformation("[{MethodName}] No expression matched.", nameof(ShouldAgentTerminateAsync));

        return Task.FromResult(false);
    }
}
