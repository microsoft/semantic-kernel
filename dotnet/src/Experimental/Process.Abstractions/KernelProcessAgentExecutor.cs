// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel.Process;

/// <summary>
/// Represents a step in a process that executes an agent.
/// </summary>
public class KernelProcessAgentExecutor : KernelProcessStep
{
    /// <summary>
    /// Invokes the agent with the provided definition.
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <returns></returns>
    [KernelFunction]
    public Task InvokeAsync(AgentDefinition agentDefinition)
    {
        return Task.CompletedTask;
    }
}
