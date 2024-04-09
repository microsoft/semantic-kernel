// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Base class for agents utilizing <see cref="Microsoft.SemanticKernel.Kernel"/> plugins or services.
/// </summary>
public abstract class KernelAgent : Agent
{
    /// <summary>
    /// The instructions of the agent (optional)
    /// </summary>
    public string? Instructions { get; init; }

    /// <summary>
    /// The <see cref="Kernel"/> containing services, plugins, and filters for use throughout the agent lifetime.
    /// </summary>
    /// <remarks>
    /// Defaults to empty Kernel, but may be overriden.
    /// </remarks>
    public Kernel Kernel { get; init; } = Kernel.CreateBuilder().Build();
}
