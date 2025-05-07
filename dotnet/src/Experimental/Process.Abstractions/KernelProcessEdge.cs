// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Delegate that represents a condition that must be met for a <see cref="KernelProcessEdge"/> to be activated.
/// </summary>
/// <param name="processEvent">The event associated with the edge.</param>
/// <param name="processState">The readonly process state.</param>
/// <returns></returns>
public delegate Task<bool> KernelProcessEdgeCondition(KernelProcessEvent processEvent, object? processState);

/// <summary>
/// A serializable representation of an edge between a source <see cref="KernelProcessStep"/> and a <see cref="KernelProcessFunctionTarget"/>.
/// </summary>
[DataContract]
[KnownType(typeof(KernelProcessFunctionTarget))]
public sealed class KernelProcessEdge
{
    /// <summary>
    /// The unique identifier of the source Step.
    /// </summary>
    [DataMember]
    public string SourceStepId { get; init; }

    /// <summary>
    /// The collection of <see cref="KernelProcessFunctionTarget"/>s that are the output of the source Step.
    /// </summary>
    [DataMember]
    public KernelProcessFunctionTarget OutputTarget { get; init; }

    /// <summary>
    /// The unique identifier for the group of edges. This may be null if the edge is not part of a group.
    /// </summary>
    [DataMember]
    public string? GroupId { get; init; }

    /// <summary>
    /// The condition that must be met for the edge to be activated.
    /// </summary>
    public KernelProcessEdgeCondition Condition { get; init; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcessEdge"/> class.
    /// </summary>
    public KernelProcessEdge(string sourceStepId, KernelProcessFunctionTarget outputTarget, string? groupId = null, KernelProcessEdgeCondition? condition = null)
    {
        Verify.NotNullOrWhiteSpace(sourceStepId);
        Verify.NotNull(outputTarget);

        this.SourceStepId = sourceStepId;
        this.OutputTarget = outputTarget;
        this.GroupId = groupId;
        this.Condition = condition ?? ((_, _) => Task.FromResult(true));
    }
}
