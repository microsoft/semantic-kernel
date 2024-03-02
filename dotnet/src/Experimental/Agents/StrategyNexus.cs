// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Strategy based agent turn-taking.
/// </summary>
public sealed class StrategyNexus : AgentNexus
{
    private readonly List<KernelAgent> _agents;
    private readonly NexusStrategy _strategy;

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
        if (!this._agents.Any(a => a.Id == agent.Id)) // $$$ PERF / LOOP
        {
            this._agents.Add(agent);
        }
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchornous enumeration of messages.</returns>
    public async Task<IAsyncEnumerable<ChatMessageContent>> InvokeAsync(string? input = null, CancellationToken cancellationToken = default)
    {
        // Identify next agent using strategy
        var agent = await this._strategy.NextAgentAsync().ConfigureAwait(false);

        return base.InvokeAgentAsync(agent, input, cancellationToken);
    }

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Asynchornous enumeration of messages.</returns>
    public async Task<IAsyncEnumerable<ChatMessageContent>> InvokeAsync(ChatMessageContent? input = null, CancellationToken cancellationToken = default)
    {
        // Identify next agent using strategy
        var agent = await this._strategy.NextAgentAsync().ConfigureAwait(false);

        return base.InvokeAgentAsync(agent, input, cancellationToken);
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="StrategyNexus"/> class.
    /// </summary>
    /// <param name="strategy">The agent selection strategy.</param>
    /// <param name="agents">The agents initially participating in the nexus.</param>
    public StrategyNexus(NexusStrategy strategy, params KernelAgent[] agents)
    {
        this._agents = [.. agents];
        this._strategy = strategy;

        this._strategy.Bind(this);
    }
}
