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

    /// <summary>
    /// Gets the kernel scoped to the current invocation.
    /// </summary>
    /// <param name="agent">The <see cref="Agent"/> whose kernel is used as a fallback if <paramref name="options"/> does not specify one.</param>
    /// <param name="options">The <see cref="AgentInvokeOptions"/> instance containing invocation-specific options. May be <c>null</c>.</param>
    /// <returns>
    /// The <see cref="Kernel"/> instance to use for the current invocation. Returns the kernel from <paramref name="options"/> if specified; otherwise, returns the kernel from <paramref name="agent"/>.
    /// </returns>
    public static Kernel GetKernel(this Agent agent, AgentInvokeOptions? options) => options?.Kernel ?? agent.Kernel;
}
