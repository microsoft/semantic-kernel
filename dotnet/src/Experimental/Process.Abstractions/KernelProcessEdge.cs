// Copyright (c) Microsoft. All rights reserved.

using System.Runtime.Serialization;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

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
    public KernelProcessTarget OutputTarget { get; init; }

    /// <summary>
    /// The unique identifier for the group of edges. This may be null if the edge is not part of a group.
    /// </summary>
    [DataMember]
    public string? GroupId { get; init; }

    /// <summary>
    /// The condition that must be met for the edge to be activated.
    /// </summary>
    public KernelProcessEdgeCondition? Condition { get; init; }

    /// <summary>
    /// The list of variable updates to be performed when the edge fires.
    /// </summary>
    public VariableUpdate? Update { get; init; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcessEdge"/> class.
    /// </summary>
    public KernelProcessEdge(string sourceStepId, KernelProcessTarget outputTarget, string? groupId = null, KernelProcessEdgeCondition? condition = null, /*Dictionary<string, object?>? metadata = null,*/ VariableUpdate? update = null)
    {
        Verify.NotNullOrWhiteSpace(sourceStepId);
        Verify.NotNull(outputTarget);

        this.SourceStepId = sourceStepId;
        this.OutputTarget = outputTarget;
        this.GroupId = groupId;
        this.Condition = condition;
        //this.Metadata = metadata ?? [];
        this.Update = update;
    }
}
