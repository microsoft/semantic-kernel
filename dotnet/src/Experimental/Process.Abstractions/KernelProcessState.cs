// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of a process.
/// </summary>
public sealed class KernelProcessState : KernelProcessStepState
public sealed record KernelProcessState : KernelProcessStepState
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessStepState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessState(string name, string? id = null)
        : base(name, id)
    {
    }
}
