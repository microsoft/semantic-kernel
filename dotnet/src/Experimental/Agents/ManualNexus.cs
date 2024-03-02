// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Explicit agent turn-taking (managed by caller).
/// </summary>
public sealed class ManualNexus : AgentNexus
{
    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public Task<IAsyncEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, string? input = null, CancellationToken cancellationToken = default) =>
        Task.FromResult(base.InvokeAgentAsync(agent, input, cancellationToken));

    /// <summary>
    /// Process a discrete incremental interaction between a single <see cref="KernelAgent"/> an a <see cref="AgentNexus"/>.
    /// </summary>
    /// <param name="agent">The agent actively interacting with the nexus.</param>
    /// <param name="input">Optional user input.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns></returns>
    public Task<IAsyncEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, ChatMessageContent? input = null, CancellationToken cancellationToken = default) =>
        Task.FromResult(base.InvokeAgentAsync(agent, input, cancellationToken));
}
