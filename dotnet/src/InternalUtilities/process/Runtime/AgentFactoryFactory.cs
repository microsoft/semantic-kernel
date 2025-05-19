// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Agents.AzureAI;
using Microsoft.SemanticKernel.Agents.OpenAI;

namespace Microsoft.SemanticKernel.Process.Internal;

/// <summary>
/// A factory for creating agent threads.
/// </summary>
public static class ProcessAgentFactory
{
    /// <summary>
    /// Processes the agent definition and creates the correct derived type of <see cref="AgentFactory"/>."/>
    /// </summary>
    /// <param name="agentDefinition">An instance of <see cref="AgentDefinition"/>.</param>
    public static AgentFactory CreateAgentFactory(this AgentDefinition agentDefinition)
    {
        return agentDefinition.Type switch
        {
            AzureAIAgentFactory.AzureAIAgentType => new AzureAIAgentFactory(),
            OpenAIAssistantAgentFactory.OpenAIAssistantAgentType => new OpenAIAssistantAgentFactory(),
            ChatCompletionAgentFactory.ChatCompletionAgentType => new ChatCompletionAgentFactory(),
            _ => throw new NotSupportedException($"Agent type {agentDefinition.Type} is not supported."),
        };
    }
}
