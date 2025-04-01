// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Process.Internal;
using Microsoft.SemanticKernel.Process.Models;
using WorkflowEngine.Serialization;

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
    public KernelProcess(KernelProcessState state, IList<KernelProcessStepInfo> steps, Dictionary<string, List<KernelProcessEdge>>? edges = null)
        : base(typeof(KernelProcess), state, edges ?? [])
    {
        Verify.NotNull(steps);
        Verify.NotNullOrWhiteSpace(state.Name);

        this.Steps = [.. steps];
    }

    public static async Task<KernelProcess?> ReadFromStringAsync(string processString)
    {
        Verify.NotNullOrWhiteSpace(processString);

        try
        {
            var workflow = WorkflowSerializer.DeserializeFromYaml(processString);

            return null;
        }
        catch (Exception ex)
        {
            throw new ArgumentException("Failed to deserialize the process string.", ex);
        }
    }
}
