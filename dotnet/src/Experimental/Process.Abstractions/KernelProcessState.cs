// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of a process.
/// </summary>
[DataContract]
public sealed record KernelProcessState : KernelProcessStepState
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessState(string name, string? id = null)
        : base(name, id)
    {
    }
}
