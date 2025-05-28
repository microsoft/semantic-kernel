// Copyright (c) Microsoft. All rights reserved.
using System.Runtime.Serialization;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A serializable representation of a Dapr Proxy.
/// </summary>
[KnownType(typeof(KernelProcessEdge))]
[KnownType(typeof(KernelProcessStepState))]
[KnownType(typeof(KernelProcessStepState<KernelProcessAgentExecutorState>))]
[KnownType(typeof(KernelProcessAgentExecutorState))]
[KnownType(typeof(ProcessAgentActions))]
public sealed record DaprAgentStepInfo : DaprStepInfo
{
    /// <summary>
    /// The agent definition associated with this step.
    /// </summary>
    public required AgentDefinition AgentDefinition { get; init; }

    /// <summary>
    /// The handler group for code-based actions.
    /// </summary>
    public required ProcessAgentActions Actions { get; init; }

    /// <summary>
    /// The inputs for this agent.
    /// </summary>
    public required NodeInputs Inputs { get; init; }

    /// <summary>
    /// Initializes a new instance of the <see cref="KernelProcessAgentStep"/> class from this instance of <see cref="DaprAgentStepInfo"/>.
    /// </summary>
    /// <returns>An instance of <see cref="KernelProcessAgentStep"/></returns>
    /// <exception cref="KernelException"></exception>
    public KernelProcessAgentStep ToKernelProcessAgentStep()
    {
        KernelProcessStepInfo processStepInfo = this.ToKernelProcessStepInfo();
        if (this.State is not KernelProcessStepState state)
        {
            throw new KernelException($"Unable to read state from agent step with name '{this.State.StepId}', Id '{this.State.RunId}' and type {this.State.GetType()}.");
        }

        return new KernelProcessAgentStep(this.AgentDefinition, this.Actions, this.State, this.Edges, threadName: "", inputs: []); // TODO: Set threadName
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="DaprAgentStepInfo"/> class from an instance of <see cref="KernelProcessAgentStep"/>.
    /// </summary>
    /// <param name="kernelAgentStepInfo">The <see cref="KernelProcessAgentStep"/> used to build the <see cref="DaprAgentStepInfo"/></param>
    /// <returns></returns>
    public static DaprAgentStepInfo FromKernelProcessAgentStep(KernelProcessAgentStep kernelAgentStepInfo)
    {
        Verify.NotNull(kernelAgentStepInfo, nameof(kernelAgentStepInfo));

        DaprStepInfo agentStepInfo = DaprStepInfo.FromKernelStepInfo(kernelAgentStepInfo);

        return new DaprAgentStepInfo
        {
            InnerStepDotnetType = agentStepInfo.InnerStepDotnetType,
            State = agentStepInfo.State,
            Edges = agentStepInfo.Edges,
            AgentDefinition = kernelAgentStepInfo.AgentDefinition,
            Inputs = new(),
            Actions = kernelAgentStepInfo.Actions,
        };
    }
}
