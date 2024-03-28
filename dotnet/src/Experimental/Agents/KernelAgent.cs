// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Experimental.Agents;

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
