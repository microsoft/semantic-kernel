// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Delegate that represents a condition that must be met for a <see cref="KernelProcessEdge"/> to be activated.
/// </summary>
/// <param name="processState">The readonly process state.</param>
/// <returns></returns>
public delegate Task<T> KernelProcessStateResolver<T>(object? processState);

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
    /// <param name="threadName"></param>
    /// <param name="inputs"></param>
    /// <param name="incomingEdgeGroups"></param>
    public KernelProcessAgentStep(AgentDefinition agentDefinition, ProcessAgentActions agentActions, KernelProcessStepState state, Dictionary<string, List<KernelProcessEdge>> edges, string threadName, Dictionary<string, Type> inputs, Dictionary<string, KernelProcessEdgeGroup>? incomingEdgeGroups = null) : base(typeof(KernelProcessAgentExecutor), state, edges, incomingEdgeGroups)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentActions);

        this.AgentDefinition = agentDefinition;
        this.Actions = agentActions;
        this.ThreadName = threadName;
        this.Inputs = inputs;
    }

    /// <summary>
    /// The optional resolver for the agent ID. This is used to determine the ID of the agent at runtime.
    /// </summary>
    public KernelProcessStateResolver<string?>? AgentIdResolver { get; init; } = null;

    /// <summary>
    /// The name of the thread this agent is associated with. Will be null if not associated with a specific thread instance.
    /// </summary>
    public string ThreadName { get; init; }

    /// <summary>
    /// The agent definition associated with this step.
    /// </summary>
    public AgentDefinition AgentDefinition { get; init; }

    /// <summary>
    /// The inputs for this agent.
    /// </summary>
    public Dictionary<string, Type> Inputs { get; init; }

    /// <summary>
    /// The handler group for code-based actions.
    /// </summary>
    public ProcessAgentActions Actions { get; init; }

    /// <summary>
    /// The human-in-the-loop mode for this agent. This determines whether the agent will wait for human input before proceeding.
    /// </summary>
    public HITLMode HumanInLoopMode { get; init; } = HITLMode.Never;
}
