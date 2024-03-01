// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// $$$
/// </summary>
/// <typeparam name="TChannel">$$$</typeparam>
/// <param name="kernel"></param>
public abstract class KernelAgent<TChannel>(Kernel kernel)
    : KernelAgent(typeof(TChannel), kernel)
        where TChannel : AgentChannel
{
    // No further specialization...
}

/// <summary>
/// $$$
/// </summary>
/// <param name="channelType"></param>
/// <param name="kernel"></param>
public abstract class KernelAgent(Type channelType, Kernel kernel)
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
    public delegate Task DefinitionCallback(KernelAgent agent, CancellationToken cancellationToken); // $$$ !!!

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
    public Kernel Kernel { get; } = kernel;

    /// <summary>
    /// The type of channel associated with the agent.
    /// </summary>
    /// <remarks>
    /// Each implementation of <see cref="KernelAgent"/> must be associated
    /// with a corresponding <see cref="AgentChannel"/>.
    /// </remarks>
    internal Type ChannelType { get; } = channelType;
}
