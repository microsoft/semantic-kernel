// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Represents the state of a <see cref="KernelProcessProxy"/>.
/// </summary>
[DataContract]
public sealed record KernelProcessProxyState : KernelProcessStepState
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessProxyState"/> class.
    /// </summary>
    /// <param name="name">The name of the associated <see cref="KernelProcessProxy"/></param>
    /// <param name="version">version id of the process step state</param>
    /// <param name="id">The Id of the associated <see cref="KernelProcessProxy"/></param>
    public KernelProcessProxyState(string name, string version, string id)
        : base(name, version, id)
    {
        Verify.NotNullOrWhiteSpace(id, nameof(id));
    }
}
