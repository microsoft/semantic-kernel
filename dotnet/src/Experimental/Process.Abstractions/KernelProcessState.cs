// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of a <see cref="KernelProcess"/>.
/// </summary>
[DataContract]
public sealed record KernelProcessState : KernelProcessStepState
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessStep"/></param>
    /// <param name="version">version id of the process step state</param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessStep"/></param>
    public KernelProcessState(string name, string version, string? id = null)
        : base(name, version, id)
    {
    }
}
