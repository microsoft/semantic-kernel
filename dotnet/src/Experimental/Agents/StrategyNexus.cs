// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Experimental.Agents.Strategy;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Strategy based agent turn-taking.
/// </summary>
public sealed class StrategyNexus : AgentNexus
{
    private readonly HashSet<string> _agentIds;
    private readonly List<KernelAgent> _agents;
    private readonly SelectionStrategy _strategy;

    /// <summary>
    /// The agents participating in the nexus.
    /// </summary>
    public IReadOnlyList<KernelAgent> Agents => this._agents.AsReadOnly();

    /// <summary>
    /// Add a <see cref="KernelAgent"/> to the nexus.
    /// </summary>
    /// <param name="agent">The <see cref="KernelAgent"/> to add.</param>
    public void AddAgent(KernelAgent agent)
    {
        if (this._agentIds.Add(agent.Id))
        {
            this._agents.Add(agent);
        }
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="input">Optional user input.</param>
    /// <param name="executionSettings">Execution settings agent interaction.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchornous enumeration of messages.</returns>
    public IAsyncEnumerable<ChatMessageContent> InvokeAsync(string? input = null, NexusExecutionSettings? executionSettings = null, CancellationToken cancellationToken = default)
    {
        var content = CreateUserMessage(input);

        return this.InvokeAsync(content, executionSettings, cancellationToken);
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="input">Optional user input.</param>
    /// <param name="executionSettings">Execution settings agent interaction.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchornous enumeration of messages.</returns>
    public async IAsyncEnumerable<ChatMessageContent> InvokeAsync(ChatMessageContent? input = null, NexusExecutionSettings? executionSettings = null, [EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        executionSettings ??= NexusExecutionSettings.Default;

        // Use the the count, if defined and positive, otherwise:
        // - Default to a maximum limit of 99 when only a criteria is defined.
        // - Default to a single iteration if no count and no criteria is defined.
        var maximumIterations =
            executionSettings.MaximumIterations > 0 ?
                executionSettings.MaximumIterations :
                executionSettings.CompletionCriteria == null ? 1 : 99;

        for (int index = 0; index < maximumIterations; index++)
        {
            // Identify next agent using strategy
            var agent = await this._strategy.NextAgentAsync().ConfigureAwait(false);

            var isComplete = false;
            await foreach (var message in base.InvokeAgentAsync(agent, input, cancellationToken))
            {
                yield return message;

                var task = executionSettings.CompletionCriteria?.Invoke(message, cancellationToken) ?? Task.FromResult(false);

                if (message.Role == AuthorRole.Assistant)
                {
                    isComplete = await task.ConfigureAwait(false);
                }

                if (isComplete)
                {
                    break;
                }
            }

            if (isComplete)
            {
                break;
            }

            input = null;
        }
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StrategyNexus"/> class.
    /// </summary>
    /// <param name="strategy">The agent selection strategy.</param>
    /// <param name="agents">The agents initially participating in the nexus.</param>
    public StrategyNexus(SelectionStrategy strategy, params KernelAgent[] agents)
    {
        this._agents = [.. agents];
        this._agentIds = [.. this._agents.Select(a => a.Id).Distinct()];
        this._strategy = strategy;

        this._strategy.Bind(this);
    }
}
