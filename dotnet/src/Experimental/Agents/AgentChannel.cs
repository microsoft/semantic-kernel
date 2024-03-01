// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// $$$
/// </summary>
public abstract class AgentChannel
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="nexus"></param>
    public abstract void Init(AgentNexus nexus);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="content"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public abstract Task RecieveAsync(IEnumerable<ChatMessageContent> content, CancellationToken cancellationToken = default);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="message"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public abstract Task<IEnumerable<ChatMessageContent>> InvokeAsync(KernelAgent agent, ChatMessageContent? message = null, CancellationToken cancellationToken = default); // $$$
}
