// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Delegate that represents a condition that must be met for a <see cref="KernelProcessEdge"/> to be activated.
/// </summary>
/// <param name="processEvent">The event associated with the edge.</param>
/// <param name="processState">The readonly process state.</param>
/// <returns></returns>
public delegate Task<bool> KernelProcessEdgeConditionCallback(KernelProcessEvent processEvent, object? processState);

/// <summary>
/// A class representing a condition that must be met for a <see cref="KernelProcessEdge"/> to be activated.
/// </summary>
public class KernelProcessEdgeCondition
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessEdgeCondition"/> class with the specified callback and optional declarative definition.
    /// </summary>
    /// <param name="callback"></param>
    /// <param name="declarativeDefinition"></param>
    public KernelProcessEdgeCondition(
        KernelProcessEdgeConditionCallback callback,
        string? declarativeDefinition = null)
    {
        this.Callback = callback;
        this.DeclarativeDefinition = declarativeDefinition;
    }

    /// <summary>
    /// The condition that must be met for the edge to be activated.
    /// </summary>
    public KernelProcessEdgeConditionCallback Callback { get; init; }

    /// <summary>
    /// The declarative definition of the condition, if any.
    /// </summary>
    public string? DeclarativeDefinition { get; init; }
}
