// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Exposes a Semantic Kernel Agent Framework <see cref="OpenAIAssistantAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
/// </summary>
public static class OpenAIAssistantAgentExtensions
{
    /// <summary>
    /// Exposes a Semantic Kernel Agent Framework <see cref="OpenAIAssistantAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
    /// </summary>
    /// <param name="assistantAgent">The Semantic Kernel <see cref="OpenAIAssistantAgent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <returns>The Semantic Kernel Agent Framework <see cref="Agent"/> exposed as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/></returns>
    [Experimental("SKEXP0110")]
    public static MAAI.AIAgent AsAIAgent(this OpenAIAssistantAgent assistantAgent)
        => assistantAgent.AsAIAgent(
            () => new OpenAIAssistantAgentThread(assistantAgent.Client),
            (json, options) =>
            {
                var agentId = JsonSerializer.Deserialize<string>(json);
                return agentId is null ? new OpenAIAssistantAgentThread(assistantAgent.Client) : new OpenAIAssistantAgentThread(assistantAgent.Client, agentId);
            },
            (thread, options) => JsonSerializer.SerializeToElement((thread as OpenAIAssistantAgentThread)?.Id));
}
