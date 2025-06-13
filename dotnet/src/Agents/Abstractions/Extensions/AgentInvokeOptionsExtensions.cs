// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel.Agents.Extensions;

/// <summary>
/// Extension methods for <see cref="AgentInvokeOptions"/>
/// </summary>
public static class AgentInvokeOptionsExtensions
{
    /// <summary>
    /// Gets the kernel scoped to the current invocation.
    /// </summary>
    /// <param name="options">The <see cref="AgentInvokeOptions"/> instance containing invocation-specific options. May be <c>null</c>.</param>
    /// <param name="agent">The <see cref="Agent"/> whose kernel is used as a fallback if <paramref name="options"/> does not specify one.</param>
    /// <returns>
    /// The <see cref="Kernel"/> instance to use for the current invocation. Returns the kernel from <paramref name="options"/> if specified; otherwise, returns the kernel from <paramref name="agent"/>.
    /// </returns>
    public static Kernel GetKernel(this AgentInvokeOptions? options, Agent agent) => options?.Kernel ?? agent.Kernel;
}
