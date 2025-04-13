// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// Represents a target for orchestration operations. This target can be either an Agent or an Orchestratable object.
/// </summary>
public enum OrchestrationTargetType
{
    /// <summary>
    /// Target is an <see cref="Agent"/>.
    /// </summary>
    Agent,

    /// <summary>
    /// Target is an <see cref="Orchestratable"/> object.
    /// </summary>
    Orchestratable,
}

/// <summary>
/// Encapsulates the target entity for orchestration, which may be an Agent or an Orchestratable object.
/// </summary>
public readonly struct OrchestrationTarget : IEquatable<OrchestrationTarget>
{
    /// <summary>
    /// Creates an orchestration target from the specified <see cref="Agent"/>.
    /// </summary>
    /// <param name="target">The agent to convert to an orchestration target.</param>
    public static implicit operator OrchestrationTarget(Agent target) => new(target);

    /// <summary>
    /// Creates an orchestration target from the specified <see cref="Orchestratable"/> object.
    /// </summary>
    /// <param name="target">The orchestratable object to convert to an orchestration target.</param>
    public static implicit operator OrchestrationTarget(Orchestratable target) => new(target);

    /// <summary>
    /// Initializes a new instance of the <see cref="OrchestrationTarget"/> struct with an <see cref="Agent"/>.
    /// </summary>
    /// <param name="agent">A target agent.</param>
    internal OrchestrationTarget(Agent agent)
    {
        this.Agent = agent;
        this.TargetType = OrchestrationTargetType.Agent;
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="OrchestrationTarget"/> struct with an <see cref="Orchestratable"/> object.
    /// </summary>
    /// <param name="orchestration">A target orchestratable object.</param>
    internal OrchestrationTarget(Orchestratable orchestration)
    {
        this.Orchestration = orchestration;
        this.TargetType = OrchestrationTargetType.Orchestratable;
    }

    /// <summary>
    /// Gets the associated <see cref="Agent"/> if this target represents an agent; otherwise, null.
    /// </summary>
    public Agent? Agent { get; }

    /// <summary>
    /// Gets the associated <see cref="Orchestratable"/> object if this target represents an orchestratable entity; otherwise, null.
    /// </summary>
    public Orchestratable? Orchestration { get; }

    /// <summary>
    /// Gets the type of the orchestration target, indicating whether it is an agent or an orchestratable object.
    /// </summary>
    public OrchestrationTargetType TargetType { get; }

    /// <summary>
    /// Determines whether the target is an <see cref="Agent"/> and retrieves it if available.
    /// </summary>
    /// <param name="orchestration">The agent reference</param>
    /// <returns>True if agent</returns>
    public bool IsAgent([NotNullWhen(true)] out Agent? orchestration)
    {
        if (this.TargetType == OrchestrationTargetType.Agent)
        {
            orchestration = this.Agent!;
            return true;
        }

        orchestration = null;
        return false;
    }

    /// <summary>
    /// Determines whether the target is an <see cref="Agent"/> and retrieves it if available.
    /// </summary>
    /// <param name="orchestration">The orchestration reference</param>
    /// <returns>True if orchestration</returns>
    public bool IsOrchestration([NotNullWhen(true)] out Orchestratable? orchestration)
    {
        if (this.TargetType == OrchestrationTargetType.Orchestratable)
        {
            orchestration = this.Orchestration!;
            return true;
        }

        orchestration = null;
        return false;
    }

    /// <inheritdoc/>
    public override readonly bool Equals(object? obj)
    {
        return obj != null && obj is OrchestrationTarget target && this.Equals(target);
    }

    /// <summary>
    /// Determines whether the specified <see cref="OrchestrationTarget"/> is equal to the current instance.
    /// </summary>
    /// <param name="other">The other orchestration target to compare.</param>
    /// <returns>true if the targets are equal; otherwise, false.</returns>
    public readonly bool Equals(OrchestrationTarget other)
    {
        return this.Agent == other.Agent && this.Orchestration == other.Orchestration;
    }

    /// <inheritdoc/>
    public override readonly int GetHashCode()
    {
        return HashCode.Combine(this.Agent?.GetHashCode() ?? 0, this.Orchestration?.GetHashCode() ?? 0);
    }

    /// <summary>
    /// Determines whether two <see cref="OrchestrationTarget"/> instances are equal.
    /// </summary>
    /// <param name="left">The first orchestration target.</param>
    /// <param name="right">The second orchestration target.</param>
    /// <returns>true if the targets are equal; otherwise, false.</returns>
    public static bool operator ==(OrchestrationTarget left, OrchestrationTarget right)
    {
        return left.Equals(right);
    }

    /// <summary>
    /// Determines whether two <see cref="OrchestrationTarget"/> instances are not equal.
    /// </summary>
    /// <param name="left">The first orchestration target.</param>
    /// <param name="right">The second orchestration target.</param>
    /// <returns>true if the targets are not equal; otherwise, false.</returns>
    public static bool operator !=(OrchestrationTarget left, OrchestrationTarget right)
    {
        return !(left == right);
    }
}
