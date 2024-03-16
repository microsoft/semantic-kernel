// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;

namespace Microsoft.SemanticKernel.Experimental.Agents.Strategy;

#pragma warning disable IDE0290 // Use primary constructor

/// <summary>
/// Semantic evaluation strategy.
/// </summary>
public sealed class SemanticSelectionStrategy : SelectionStrategy
{
    private readonly string _instructions;
    private readonly IChatCompletionService _service;
    private readonly PromptExecutionSettings? _executionSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="SemanticSelectionStrategy"/> class.
    /// </summary>
    /// <param name="service">A chat-completion service.</param>
    /// <param name="instructions">The evaluation instructions.</param>
    /// <param name="executionSettings">The execution settings for the strategy.</param>
    public SemanticSelectionStrategy(IChatCompletionService service, string instructions, PromptExecutionSettings? executionSettings = null)
    {
        this._service = service;
        this._instructions = instructions;
        this._executionSettings = executionSettings;
    }

    /// <inheritdoc/>
    public override async Task<Agent?> NextAgentAsync(CancellationToken cancellationToken)
    {
        var chat = new ChatHistory(this._instructions);

        chat.AddRange(this.Nexus.History); // $$$ TODO: PROCESS MESSAGES

        var messages =
            await this._service.GetChatMessageContentsAsync(
                chat,
                this._executionSettings,
                kernel: null,
                cancellationToken).ConfigureAwait(false);

        var agentName = messages[0].Content;

        var agent = this.Nexus.Agents.Where(a => (a.Name ?? a.Id).Equals(agentName, StringComparison.OrdinalIgnoreCase)).FirstOrDefault(); // $$$ BETTER MATCHER

        return agent;
    }
}
