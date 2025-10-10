// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Exposes a Semantic Kernel Agent Framework <see cref="OpenAIResponseAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
/// </summary>
public static class OpenAIResponseAgentExtensions
{
    /// <summary>
    /// Exposes a Semantic Kernel Agent Framework <see cref="OpenAIResponseAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
    /// </summary>
    /// <param name="responseAgent">The Semantic Kernel <see cref="OpenAIResponseAgent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <returns>The Semantic Kernel Agent Framework <see cref="Agent"/> exposed as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/></returns>
    [Experimental("SKEXP0110")]
    public static MAAI.AIAgent AsAIAgent(this OpenAIResponseAgent responseAgent)
        => responseAgent.AsAIAgent(
            () => new OpenAIResponseAgentThread(responseAgent.Client),
            (json, options) =>
            {
                var agentId = JsonSerializer.Deserialize<string>(json);
                return agentId is null ? new OpenAIResponseAgentThread(responseAgent.Client) : new OpenAIResponseAgentThread(responseAgent.Client, agentId);
            },
            (thread, options) => JsonSerializer.SerializeToElement((thread as OpenAIResponseAgentThread)?.Id));
}
