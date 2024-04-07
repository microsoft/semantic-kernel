// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base class for agents utilizing <see cref="Microsoft.SemanticKernel.Kernel"/> plugins or services.
/// </summary>
public abstract class KernelAgent : Agent
{
    /// <summary>
    /// The arguments used to optionally format <see cref="Instructions"/>.
    /// </summary>
    public KernelArguments? InstructionArguments { get; init; }

    /// <summary>
    /// The instructions of the agent (optional)
    /// </summary>
    public string? Instructions { get; init; }

    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and filters for use throughout the agent lifetime.
    /// </summary>
    public Kernel Kernel { get; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelAgent"/> class.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    protected KernelAgent(Kernel kernel)
    {
        this.Kernel = kernel;
    }
}
