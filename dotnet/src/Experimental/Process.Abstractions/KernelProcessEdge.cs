// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of an edge between a source <see cref="KernelProcessStep"/> and a <see cref="KernelProcessFunctionTarget"/>.
/// </summary>
public sealed class KernelProcessEdge
{
    /// <summary>
    /// The unique identifier of the source Step.
    /// </summary>
    public string SourceStepId { get; }

    /// <summary>
    /// The collection of <see cref="KernelProcessFunctionTarget"/>s that are the output of the source Step.
    /// </summary>
    public KernelProcessFunctionTarget OutputTarget { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcessEdge"/> class.
    /// </summary>
    public KernelProcessEdge(string sourceStepId, KernelProcessFunctionTarget outputTargets)
    {
        Verify.NotNullOrWhiteSpace(sourceStepId);
        Verify.NotNull(outputTargets);

        this.SourceStepId = sourceStepId;
        this.OutputTarget = outputTargets;
    }
}
