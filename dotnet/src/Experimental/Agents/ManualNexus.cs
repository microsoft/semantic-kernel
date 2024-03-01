// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
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
    public Task<IEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, string? input = null, CancellationToken cancellationToken = default) =>
        base.InvokeAgentAsync(agent, input, cancellationToken);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public Task<IEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, ChatMessageContent? input = null, CancellationToken cancellationToken = default) =>
        base.InvokeAgentAsync(agent, input, cancellationToken);
}
