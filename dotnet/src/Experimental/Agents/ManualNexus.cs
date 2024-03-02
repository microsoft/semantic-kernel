// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// $$$
/// </summary>
public sealed class ManualNexus : AgentNexus
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<IEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, string? input = null, CancellationToken cancellationToken = default) =>
        await base.InvokeAgentAsync(agent, input, cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false); // $$$ YUUUCK

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public async Task<IEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, ChatMessageContent? input = null, CancellationToken cancellationToken = default) =>
        await base.InvokeAgentAsync(agent, input, cancellationToken).ToArrayAsync(cancellationToken).ConfigureAwait(false); // $$$ YUUUCK
}
