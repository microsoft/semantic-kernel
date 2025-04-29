// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Json.Schema;
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
    /// <param name="agentActions"></param>
    /// <param name="state"></param>
    /// <param name="edges"></param>
    /// <param name="incomingEdgeGroups"></param>
    public KernelProcessAgentStep(AgentDefinition agentDefinition, ProcessAgentActions agentActions, KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges, Dictionary<string, KernelProcessEdgeGroup>? incomingEdgeGroups = null) : base(typeof(KernelProcessAgentExecutor), state, edges, incomingEdgeGroups)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentActions);

        this.AgentDefinition = agentDefinition;
        this.Actions = agentActions;

        // Register the state as a know type for the DataContractSerialization used by Dapr.
        KernelProcessState.RegisterDerivedType(state.GetType());
    }

    /// <summary>
    /// The agent definition associated with this step.
    /// </summary>
    public AgentDefinition AgentDefinition { get; init; }

    /// <summary>
    /// The inputs for this agent.
    /// </summary>
    public Dictionary<string, JsonSchema>? Inputs { get; init; }

    /// <summary>
    /// The handler group for code-based actions.
    /// </summary>
    public ProcessAgentActions Actions { get; init; }
}
