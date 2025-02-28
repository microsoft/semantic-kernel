// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a ProcessProxy.
/// </summary>
public sealed record KernelProcessProxy : KernelProcessStepInfo
{
    /// <summary>
    /// Proxy metadata used for linking specific SK events to external events and viceversa
    /// </summary>
    public KernelProcessProxyStateMetadata? ProxyMetadata { get; init; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="edges">The edges for the map.</param>
    public KernelProcessProxy(KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges)
        : base(typeof(KernelProxyStep), state, edges)
    {
        Verify.NotNullOrWhiteSpace(state.Name, $"{nameof(state)}.{nameof(KernelProcessStepState.Name)}");
        Verify.NotNullOrWhiteSpace(state.Id, $"{nameof(state)}.{nameof(KernelProcessStepState.Id)}");
    }
}
