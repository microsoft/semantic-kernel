// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of a <see cref="KernelProcessMap"/>.
/// </summary>
[DataContract]
public sealed record KernelProcessMapState : KernelProcessStepState
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessMapState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessMap"/></param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessMap"/></param>
    public KernelProcessMapState(string name, string id)
        : base(name, id)
    {
        Verify.NotNullOrWhiteSpace(id, nameof(id));
    }
}
