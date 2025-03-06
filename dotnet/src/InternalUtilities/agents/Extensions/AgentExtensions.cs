// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Extension methods for <see cref="Agent"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class AgentExtensions
{
    /// <summary>
    /// Provides a name for the agent, even if it's the identifier.
    /// (since <see cref="Agent.Name"/> allows null)
    /// </summary>
    /// <param name="agent">The target agent</param>
    /// <returns>The agent name as a non-empty string</returns>
    public static string GetName(this Agent agent) => agent.Name ?? agent.Id;

    /// <summary>
    /// Provides the display name of the agent.
    /// </summary>
    /// <param name="agent">The target agent</param>
    /// <remarks>
    /// Currently, it's intended for telemetry purposes only.
    /// </remarks>
    public static string GetDisplayName(this Agent agent) => !string.IsNullOrWhiteSpace(agent.Name) ? agent.Name! : "UnnamedAgent";
}
