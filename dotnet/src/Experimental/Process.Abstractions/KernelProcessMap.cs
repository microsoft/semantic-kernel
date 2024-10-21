// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Process.
/// </summary>
public sealed record KernelProcessMap : KernelProcessStepInfo
{
    /// <summary>
    /// The discrete map operation.
    /// </summary>
    public KernelProcess MapStep { get; }

    /// <summary>
    /// The event that signals the completion of the map operation.
    /// </summary>
    public string CompleteEventId { get; }

    /// <summary>
    /// The name of the input parameter for the map operation.
    /// </summary>
    public string InputParameterName { get; }

    /// <summary>
    /// Creates a new instance of the <see cref="KernelProcess"/> class.
    /// </summary>
    /// <param name="state">The process state.</param>
    /// <param name="step">The discrete map operation.</param>
    /// <param name="completeEventId">The event that signals the completion of the map operation.</param>
    /// <param name="inputParameter">name of the input parameter for the map operation.</param>
    public KernelProcessMap(KernelProcessMapState state, KernelProcess step/*, string startEventId*/, string completeEventId, string inputParameter)
        : base(typeof(KernelProcessMap), state, [])
    {
        Verify.NotNull(step);
        Verify.NotNullOrWhiteSpace(state.Name);

        this.MapStep = step;
        this.CompleteEventId = completeEventId;
        this.InputParameterName = inputParameter;
    }
}
