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
    /// <param name="content"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public abstract Task RecieveAsync(IEnumerable<ChatMessageContent> content, CancellationToken cancellationToken = default);

    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="input"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(
        KernelAgent agent,
        ChatMessageContent? input = null, // $$$ USER PROXY
        CancellationToken cancellationToken = default);
}
