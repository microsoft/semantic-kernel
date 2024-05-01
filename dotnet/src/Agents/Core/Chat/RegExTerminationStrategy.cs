// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Signals termination when the most recent message matches against the defined regular expressions
/// for the specified agent (if provided).
/// </summary>
/// <param name="expressions">A list of regular expressions, that if</param>
public sealed class RegExTerminationStrategy(params string[] expressions) : TerminationStrategy
{
    private readonly string[] _expressions = expressions;

    /// <inheritdoc/>
    protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // Most recent message
        var message = history[history.Count - 1];

        this.Logger.LogDebug("[{MethodName}] Evaluating expressions: {ExpressionCount}", nameof(ShouldAgentTerminateAsync), this._expressions.Length);

        // Evaluate expressions for match
        foreach (var expression in this._expressions)
        {
            this.Logger.LogDebug("[{MethodName}] Evaluating expression: {Expression}", nameof(ShouldAgentTerminateAsync), expression);

            if (Regex.IsMatch(message.Content, expression))
            {
                this.Logger.LogInformation("[{MethodName}] Expression matched: {Expression}", nameof(ShouldAgentTerminateAsync), expression);

                return Task.FromResult(true);
            }
        }

        this.Logger.LogInformation("[{MethodName}] No expression matched.", nameof(ShouldAgentTerminateAsync));

        return Task.FromResult(false);
    }
}
