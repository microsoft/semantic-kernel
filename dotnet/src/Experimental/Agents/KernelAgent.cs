// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Base class for agents.
/// </summary>
/// <remarks>
/// Initializes a new instance of the <see cref="KernelAgent"/> class.
/// </remarks>
/// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
/// <param name="instructions">The agent instructions</param>
public abstract class KernelAgent(Kernel kernel, string? instructions = null) : Agent
{
    /// <summary>
    /// The arguments used to optionally format <see cref="Instructions"/>.
    /// </summary>
    public KernelArguments? InstructionArguments { get; set; }

    /// <summary>
    /// The instructions of the agent (optional)
    /// </summary>
    public string? Instructions => instructions;

    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.
    /// </summary>
    public Kernel Kernel { get; } = kernel;
}
