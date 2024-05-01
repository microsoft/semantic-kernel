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
public sealed class RegExTerminationStrategy : TerminationStrategy
{
    private readonly string[] _expressions;

    /// <inheritdoc/>
    protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        this.Logger.LogInformation("Evaluating termination for agent {AgentId}.", agent.Id); // %%% FIX LOGGING

        // Most recent message
        var message = history[history.Count - 1];

        // Evaluate expressions for match
        foreach (var expression in this._expressions)
        {
            this.Logger.LogDebug("Evaluating expression: {Expression} against message: {Message}", expression, message.Content); // %%% FIX LOGGING
            if (Regex.IsMatch(message.Content, expression))
            {
                this.Logger.LogInformation("Expression: {Expression} matched message: {Message}", expression, message.Content); // %%% FIX LOGGING
                return Task.FromResult(true);
            }
        }

        this.Logger.LogInformation("No expression matched message: {Message}", message.Content); // %%% FIX LOGGING
        return Task.FromResult(false);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="RegExTerminationStrategy"/> class.
    /// </summary>
    /// <param name="expressions">A list of regular expressions, that if</param>
    public RegExTerminationStrategy(params string[] expressions)
    {
        this._expressions = expressions;
    }
}
