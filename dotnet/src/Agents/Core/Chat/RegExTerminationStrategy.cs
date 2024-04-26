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
/// <remarks>
/// Initializes a new instance of the <see cref="RegExTerminationStrategy"/> class.
/// </remarks>
/// <param name="expressions">A list of regular expressions, that if</param>
/// <param name="logger">The logger.</param>
public sealed class RegExTerminationStrategy(string[] expressions, ILogger<RegExTerminationStrategy> logger) : TerminationStrategy(logger)
{
    private readonly ILogger<RegExTerminationStrategy> _logger = logger;
    private readonly string[] _expressions = expressions;

    /// <inheritdoc/>
    protected override Task<bool> ShouldAgentTerminateAsync(Agent agent, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        // %%% TAO - CONSIDER THIS SECTION FOR LOGGING
        this._logger.LogInformation("Evaluating termination for agent {AgentId}.", agent.Id);

        // Most recent message
        var message = history[history.Count - 1];

        // Evaluate expressions for match
        foreach (var expression in this._expressions)
        {
            this._logger.LogDebug("Evaluating expression: {Expression} against message: {Message}", expression, message.Content);
            if (Regex.IsMatch(message.Content, expression))
            {
                this._logger.LogInformation("Expression: {Expression} matched message: {Message}", expression, message.Content);
                return Task.FromResult(true);
            }
        }

        this._logger.LogInformation("No expression matched message: {Message}", message.Content);
        return Task.FromResult(false);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="RegExTerminationStrategy"/> class.
    /// </summary>
    /// <param name="logger">The logger.</param>
    public RegExTerminationStrategy(ILogger<RegExTerminationStrategy> logger) : this([], logger) { }
}
