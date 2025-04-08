// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for creating KernelPlugin instances from agents.
/// </summary>
public static class KernelPluginFactoryExtensions
{
    /// <summary>
    /// Creates a plugin from a collection of agents. Each agent is converted into a KernelFunction via AgentKernelFunctionFactory.
    /// </summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="agents">A collection of agents to include in the plugin.</param>
    /// <returns>A KernelPlugin with functions derived from the provided agents.</returns>
    /// <exception cref="ArgumentNullException">Thrown when agents is null.</exception>
    public static KernelPlugin CreateFromFunctions(string pluginName, string? description, IEnumerable<Agent> agents)
    {
        if (agents == null)
        {
            throw new ArgumentNullException(nameof(agents));
        }

        var functions = new List<KernelFunction>();
        foreach (var agent in agents)
        {
            functions.Add(AgentKernelFunctionFactory.CreateFromAgent(agent));
        }

        // Call the public method in SemanticKernel.Core
        return KernelPluginFactory.CreateFromFunctions(pluginName, description, functions);
    }

    /// <summary>
    /// Creates a plugin from an array of agents. Each agent is converted into a KernelFunction via AgentKernelFunctionFactory.
    /// </summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="agents">The agents to include in the plugin.</param>
    /// <returns>A KernelPlugin with functions derived from the provided agents.</returns>
    public static KernelPlugin CreateFromFunctions(string pluginName, params Agent[] agents) =>
        CreateFromFunctions(pluginName, description: null, agents);
}
