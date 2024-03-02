// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Base class for agents.
/// </summary>
/// <typeparam name="TChannel">The type of <see cref="AgentChannel"/> appropriate for the agent type.</typeparam>
public abstract class KernelAgent<TChannel> : KernelAgent
        where TChannel : AgentChannel
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    protected KernelAgent(Kernel kernel)
        : base(typeof(TChannel), kernel)
    {
        // Nothing to do...
    }
}

/// <summary>
/// Base class for agents.
/// </summary>
public abstract class KernelAgent
{
    /// <summary>
    /// The description of the agent (optional)
    /// </summary>
    public abstract string? Description { get; }

    /// <summary>
    /// The identifier of the agent (optional)
    /// </summary>
    public abstract string Id { get; }

    /// <summary>
    /// The instructions of the agent (optional)
    /// </summary>
    public abstract string? Instructions { get; }

    /// <summary>
    /// The name of the agent (optional)
    /// </summary>
    public abstract string? Name { get; }

    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; }

    /// <summary>
    /// The type of channel associated with the agent.
    /// </summary>
    /// <remarks>
    /// Each implementation of <see cref="KernelAgent"/> must be associated
    /// with a corresponding <see cref="AgentChannel"/>.
    /// </remarks>
    internal Type ChannelType { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelAgent"/> class.
    /// </summary>
    /// <param name="channelType">The type of <see cref="AgentChannel"/> appropriate for the agent type.</param>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    protected KernelAgent(Type channelType, Kernel kernel)
    {
        this.Kernel = kernel;
        this.ChannelType = channelType;
    }

    /// <summary>
    /// Produce the an <see cref="AgentChannel"/> appropriate for the agent type.
    /// </summary>
    /// <param name="nexus">The <see cref="AgentNexus"/> requesting the channel.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="AgentChannel"/> appropriate for the agent type.</returns>
    protected internal abstract Task<AgentChannel> CreateChannelAsync(AgentNexus nexus, CancellationToken cancellationToken);
}
