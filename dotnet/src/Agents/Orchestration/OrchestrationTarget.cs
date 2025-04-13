// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Agents.Orchestration;

/// <summary>
/// %%% COMMENT
/// </summary>
public enum OrchestrationTargetType
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    Agent,

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    Orchestratable,
}

/// <summary>
/// %%% COMMENT
/// </summary>
public readonly struct OrchestrationTarget : IEquatable<OrchestrationTarget>
{
    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public static implicit operator OrchestrationTarget(Agent target) => new(target);

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public static implicit operator OrchestrationTarget(Orchestratable target) => new(target);

    internal OrchestrationTarget(Agent agent)
    {
        this.Agent = agent;
        this.TargetType = OrchestrationTargetType.Agent;
    }

    internal OrchestrationTarget(Orchestratable orchestration)
    {
        this.Orchestration = orchestration;
        this.TargetType = OrchestrationTargetType.Orchestratable;
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public Agent? Agent { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public Orchestratable? Orchestration { get; }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    public OrchestrationTargetType TargetType { get; }

    /// <inheritdoc/>
    public override readonly bool Equals(object? obj)
    {
        return obj != null && this.Equals(obj is OrchestrationTarget);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="other"></param>
    /// <returns></returns>
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
    /// %%% COMMENT
    /// </summary>
    /// <param name="left"></param>
    /// <param name="right"></param>
    /// <returns></returns>
    public static bool operator ==(OrchestrationTarget left, OrchestrationTarget right)
    {
        return left.Equals(right);
    }

    /// <summary>
    /// %%% COMMENT
    /// </summary>
    /// <param name="left"></param>
    /// <param name="right"></param>
    /// <returns></returns>
    public static bool operator !=(OrchestrationTarget left, OrchestrationTarget right)
    {
        return !(left == right);
    }
}
