// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents a step in a process that is an agent.
/// </summary>
public record KernelProcessAgentStep : KernelProcessStepInfo
{
    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessAgentStep"/> class.
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <param name="state"></param>
    /// <param name="edges"></param>
    /// <param name="incomingEdgeGroups"></param>
    public KernelProcessAgentStep(AgentDefinition agentDefinition, KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges, Dictionary<string, KernelProcessEdgeGroup>? incomingEdgeGroups = null) : base(typeof(KernelProcessAgentExecutor), state, edges, incomingEdgeGroups)
    {
        Verify.NotNull(agentDefinition);
        this.AgentDefinition = agentDefinition;
    }

    /// <summary>
    /// The agent definition associated with this step.
    /// </summary>
    public AgentDefinition AgentDefinition { get; init; }

    /// <summary>
    /// The optional handler group for OnComplete events.
    /// </summary>
    public KernelProcessDeclarativeConditionHandler? OnComplete { get; init; }

    /// <summary>
    /// The optional handler group for OnError events.
    /// </summary>
    public KernelProcessDeclarativeConditionHandler? OnError { get; init; }
}
