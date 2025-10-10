// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents.A2A;

/// <summary>
/// Exposes a Semantic Kernel Agent Framework <see cref="A2AAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
/// </summary>
public static class A2AAgentExtensions
{
    /// <summary>
    /// Exposes a Semantic Kernel Agent Framework <see cref="A2AAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
    /// </summary>
    /// <param name="a2aAgent">The Semantic Kernel <see cref="A2AAgent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <returns>The Semantic Kernel Agent Framework <see cref="Agent"/> exposed as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/></returns>
    [Experimental("SKEXP0110")]
    public static MAAI.AIAgent AsAIAgent(this A2AAgent a2aAgent)
        => a2aAgent.AsAIAgent(
            () => new A2AAgentThread(a2aAgent.Client),
            (json, options) =>
            {
                var agentId = JsonSerializer.Deserialize<string>(json);
                return agentId is null ? new A2AAgentThread(a2aAgent.Client) : new A2AAgentThread(a2aAgent.Client, agentId);
            },
            (thread, options) => JsonSerializer.SerializeToElement((thread as A2AAgentThread)?.Id));
}
