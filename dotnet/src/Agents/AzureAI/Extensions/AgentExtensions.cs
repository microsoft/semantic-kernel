// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Extension methods for <see cref="Agent"/>.
/// </summary>
internal static class AgentExtensions
{
    /// <summary>
    /// Provides a name for the agent, even if it's the identifier.
    /// (since <see cref="Agent.Name"/> allows null)
    /// </summary>
    /// <param name="agent">The target agent</param>
    /// <returns>The agent name as a non-empty string</returns>
    public static string GetName(this Agent agent)
    {
        return agent.Name ?? agent.Id;
    }
}
