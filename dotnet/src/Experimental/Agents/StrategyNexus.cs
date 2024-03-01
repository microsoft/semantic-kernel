// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// $$$
/// </summary>
public sealed class StrategyNexus : AgentNexus
{
    private readonly List<KernelAgent> _agents;
    private readonly NexusStrategy _strategy;

    /// <summary>
    /// $$$
    /// </summary>
    public IReadOnlyList<KernelAgent> Agents => this._agents.AsReadOnly();

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    public void AddAgent(KernelAgent agent)
    {
        if (!this._agents.Any(a => a.Id == agent.Id)) // $$$ PERF / LOOP
        {
            this._agents.Add(agent);
        }
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<IEnumerable<ChatMessageContent>> InvokeAsync(string? input = null, CancellationToken cancellationToken = default)
    {
        // Identify next agent using strategy
        var agent = await this._strategy.NextAgentAsync().ConfigureAwait(false);

        return await base.InvokeAgentAsync(agent, input, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<IEnumerable<ChatMessageContent>> InvokeAsync(ChatMessageContent? input = null, CancellationToken cancellationToken = default)
    {
        // Identify next agent using strategy
        var agent = await this._strategy.NextAgentAsync().ConfigureAwait(false);

        return await base.InvokeAgentAsync(agent, input, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="strategy"></param>
    /// <param name="agents"></param>
    public StrategyNexus(NexusStrategy strategy, params KernelAgent[] agents)
    {
        this._agents = [.. agents];
        this._strategy = strategy;

        this._strategy.Bind(this);
    }
}
