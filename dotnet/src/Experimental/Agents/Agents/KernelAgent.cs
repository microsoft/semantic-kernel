// Copyright (c) Microsoft. All rights reserved.
using System;

namespace Microsoft.SemanticKernel.Experimental.Agents.Agents;

/// <summary>
/// Base class for agents.
/// </summary>
/// <typeparam name="TChannel">The type of <see cref="AgentChannel"/> appropriate for the agent type.</typeparam>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelAgent"/> class.
/// </remarks>
/// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
public abstract class KernelAgent<TChannel>(Kernel kernel)
                        : KernelAgent(kernel)
                            where TChannel : AgentChannel
{
    /// <summary>
    /// The type of channel associated with the agent, should one be required.
    /// </summary>
    /// <remarks>
    /// Each implementation of <see cref="KernelAgent"/> must be associated
    /// with a corresponding <see cref="AgentChannel"/>.
    /// </remarks>
    protected internal override Type ChannelType => typeof(TChannel);
}

/// <summary>
/// Base class for agents.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelAgent"/> class.
/// </remarks>
/// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
public abstract class KernelAgent(Kernel kernel) : Agent
{
    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; } = kernel;
}
