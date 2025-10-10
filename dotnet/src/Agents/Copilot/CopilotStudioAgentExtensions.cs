// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using MAAI = Microsoft.Agents.AI;

namespace Microsoft.SemanticKernel.Agents.Copilot;

/// <summary>
/// Exposes a Semantic Kernel Agent Framework <see cref="CopilotStudioAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
/// </summary>
public static class CopilotStudioAgentExtensions
{
    /// <summary>
    /// Exposes a Semantic Kernel Agent Framework <see cref="CopilotStudioAgent"/> as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.
    /// </summary>
    /// <param name="copilotStudioAgent">The Semantic Kernel <see cref="CopilotStudioAgent"/> to expose as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/>.</param>
    /// <returns>The Semantic Kernel Agent Framework <see cref="Agent"/> exposed as a Microsoft Agent Framework <see cref="MAAI.AIAgent"/></returns>
    [Experimental("SKEXP0110")]
    public static MAAI.AIAgent AsAIAgent(this CopilotStudioAgent copilotStudioAgent)
        => copilotStudioAgent.AsAIAgent(
            () => new CopilotStudioAgentThread(copilotStudioAgent.Client),
            (json, options) =>
            {
                var agentId = JsonSerializer.Deserialize<string>(json);
                return agentId is null ? new CopilotStudioAgentThread(copilotStudioAgent.Client) : new CopilotStudioAgentThread(copilotStudioAgent.Client, agentId);
            },
            (thread, options) => JsonSerializer.SerializeToElement((thread as CopilotStudioAgentThread)?.Id));
}
