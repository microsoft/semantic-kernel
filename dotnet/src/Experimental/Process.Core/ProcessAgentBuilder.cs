// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Process.Models;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Builder for a process step that represents an agent.
/// </summary>
public class ProcessAgentBuilder : ProcessStepBuilder<KernelProcessAgentExecutor>
{
    private readonly AgentDefinition _agentDefinition;

    /// <summary>
    /// Creates a new instance of the <see cref="ProcessAgentBuilder"/> class.
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <exception cref="KernelException"></exception>
    public ProcessAgentBuilder(AgentDefinition agentDefinition) : base(agentDefinition.Id ?? throw new KernelException("AgentDefinition Id must be set"))
    {
        Verify.NotNull(agentDefinition);
        this._agentDefinition = agentDefinition;
    }

    internal override KernelProcessStepInfo BuildStep(KernelProcessStepStateMetadata? stateMetadata = null)
    {
        KernelProcessMapStateMetadata? mapMetadata = stateMetadata as KernelProcessMapStateMetadata;

        // Build the edges first
        var builtEdges = this.Edges.ToDictionary(kvp => kvp.Key, kvp => kvp.Value.Select(e => e.Build()).ToList());
        var state = new KernelProcessStepState(this.Name, "1.0", this.Id);

        return new KernelProcessAgentStep(this._agentDefinition, state, builtEdges);
    }
}
