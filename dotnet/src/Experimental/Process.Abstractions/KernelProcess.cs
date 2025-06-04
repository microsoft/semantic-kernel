// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public sealed record KernelProcess : KernelProcessStepInfo
{
    /// <summary>
    /// The collection of Steps in the Process.
    /// </summary>
    public IList<KernelProcessStepInfo> Steps { get; }

    /// <summary>
    /// The collection of Threads in the Process.
    /// </summary>
    public IReadOnlyDictionary<string, KernelProcessAgentThread> Threads { get; init; } = new Dictionary<string, KernelProcessAgentThread>();

    /// <summary>
    /// The type of the user state. This is used to identify the underlying state type.
    /// </summary>
    public Type? UserStateType { get; init; } = null;

    /// <summary>
    /// Captures Kernel Process State into <see cref="KernelProcessStateMetadata"/> after process has run
    /// </summary>
    /// <returns><see cref="KernelProcessStateMetadata"/></returns>
    public KernelProcessStateMetadata ToProcessStateMetadata()
    {
        return ProcessStateMetadataFactory.KernelProcessToProcessStateMetadata(this);
    }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="steps">The steps of the process.</param>
    /// <param name="edges">The edges of the process.</param>
    /// <param name="threads">The threads associated with the process.</param>
    public KernelProcess(KernelProcessState state, IList<KernelProcessStepInfo> steps, Dictionary<string, List<KernelProcessEdge>>? edges = null, IReadOnlyDictionary<string, KernelProcessAgentThread>? threads = null)
        : base(typeof(KernelProcess), state, edges ?? [])
    {
        Verify.NotNull(steps);
        Verify.NotNullOrWhiteSpace(state.Name);

        this.Steps = [.. steps];
    }
}
