// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Exposes a Semantic Kernel Agent Framework <see cref="AzureAIAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
/// </summary>
public static class AzureAIAgentExtensions
{
    /// <summary>
    /// Exposes a Semantic Kernel Agent Framework <see cref="AzureAIAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
    /// </summary>
    /// <param name="azureAIAgent">The Semantic Kernel <see cref="AzureAIAgent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <returns>The Semantic Kernel Agent Framework <see cref="Agent"/> exposed as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/></returns>
    [Experimental("SKEXP0110")]
    public static MAAI.AIAgent AsAIAgent(this AzureAIAgent azureAIAgent)
        => azureAIAgent.AsAIAgent(
            () => new AzureAIAgentThread(azureAIAgent.Client),
            (json, options) =>
            {
                var agentId = JsonSerializer.Deserialize<string>(json);
                return agentId is null ? new AzureAIAgentThread(azureAIAgent.Client) : new AzureAIAgentThread(azureAIAgent.Client, agentId);
            },
            (thread, options) => JsonSerializer.SerializeToElement((thread as AzureAIAgentThread)?.Id));
}
