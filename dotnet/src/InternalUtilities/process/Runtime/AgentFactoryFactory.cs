// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.OpenAI;

namespace Microsoft.SemanticKernel.Process.Internal;

/// <summary>
/// A factory for creating agent threads.
/// </summary>
public static class ProcesAgentFactory
{
    /// <summary>
    /// Processes the agent definition and creates the correct derived type of <see cref="AgentFactory"/>."/>
    /// </summary>
    /// <param name="agentDefinition"></param>
    /// <returns></returns>
    /// <exception cref="NotSupportedException"></exception>
    public static AgentFactory CreateAgentFactoryAsync(this AgentDefinition agentDefinition)
    {
        return agentDefinition.Type switch
        {
            AzureAIAgentFactory.AzureAIAgentType => new AzureAIAgentFactory(),
            OpenAIAssistantAgentFactory.OpenAIAssistantAgentType => new OpenAIAssistantAgentFactory(),
            _ => throw new NotSupportedException($"Agent type {agentDefinition.Type} is not supported."),
        };
    }
}
