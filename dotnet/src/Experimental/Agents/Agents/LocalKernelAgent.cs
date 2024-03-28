// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

/// <summary>
/// A <see cref="KernelAgent"/> specialization bound to <see cref="LocalChannel"/>.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="LocalKernelAgent"/> class.
/// </remarks>
/// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
public abstract class LocalKernelAgent(Kernel kernel) : KernelAgent(kernel), ILocalAgent
{
    /// <inheritdoc/>
    protected internal sealed override Type ChannelType => typeof(LocalChannel);

    /// <inheritdoc/>
    protected internal sealed override Task<AgentChannel> CreateChannelAsync(AgentNexus nexus, CancellationToken cancellationToken)
    {
        return Task.FromResult<AgentChannel>(new LocalChannel(this));
    }

    /// <inheritdoc/>
    public abstract IAsyncEnumerable<ChatMessageContent> InvokeAsync(IEnumerable<ChatMessageContent> history, CancellationToken cancellationToken);
}
