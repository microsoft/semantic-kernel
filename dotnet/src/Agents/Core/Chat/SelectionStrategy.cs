// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Agents.Chat;

/// <summary>
/// Provides a base strategy class for selecting the next agent for an <see cref="AgentGroupChat"/>.
/// </summary>
[Experimental("SKEXP0110")]
public abstract class SelectionStrategy
{
    /// <summary>
    /// Gets a value that indicates if an agent has been selected (first time).
    /// </summary>
    protected bool HasSelected { get; private set; }

    /// <summary>
    /// Gets or sets an optional agent for initial selection.
    /// </summary>
    /// <remarks>
    /// Setting this property is useful to avoid latency in initial agent selection.
    /// </remarks>
    public Agent? InitialAgent { get; set; }

    /// <summary>
    /// Gets the <see cref="ILogger"/> associated with the <see cref="SelectionStrategy"/>.
    /// </summary>
    protected internal ILogger Logger { get; internal set; } = NullLogger.Instance;

    /// <summary>
    /// Determines which agent goes next.
    /// </summary>
    /// <param name="agents">The agents participating in chat.</param>
    /// <param name="history">The chat history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The agent that will take the next turn.</returns>
    public async Task<Agent> NextAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default)
    {
        if (agents.Count == 0 && this.InitialAgent == null)
        {
            throw new KernelException("Agent Failure - No agents present to select.");
        }

        Agent agent =
            (!this.HasSelected && this.InitialAgent != null) ?
                this.InitialAgent :
                await this.SelectAgentAsync(agents, history, cancellationToken).ConfigureAwait(false);

        this.HasSelected = true;

        return agent;
    }

    /// <summary>
    /// Determines which agent goes next.
    /// </summary>
    /// <param name="agents">The agents participating in chat.</param>
    /// <param name="history">The chat history.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The agent that will take the next turn.</returns>
    protected abstract Task<Agent> SelectAgentAsync(IReadOnlyList<Agent> agents, IReadOnlyList<ChatMessageContent> history, CancellationToken cancellationToken = default);
}
