// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Agents;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for creating KernelPlugin instances from agents.
/// </summary>
[Experimental("SKEXP0110")]
public static class AgentKernelPluginFactory
{
    /// <summary>
    /// Creates a plugin from a collection of agents. Each agent is converted into a KernelFunction via AgentKernelFunctionFactory.
    /// </summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="description">A description of the plugin.</param>
    /// <param name="agents">A collection of agents to include in the plugin.</param>
    /// <returns>A KernelPlugin with functions derived from the provided agents.</returns>
    /// <exception cref="ArgumentNullException">Thrown when agents is null.</exception>
    public static KernelPlugin CreateFromAgents(string pluginName, string? description, IEnumerable<Agent> agents)
    {
        if (agents == null)
        {
            throw new ArgumentNullException(nameof(agents));
        }

        KernelFunction[] functions = agents
            .Select(agent => AgentKernelFunctionFactory.CreateFromAgent(agent))
            .ToArray();

        return KernelPluginFactory.CreateFromFunctions(pluginName, description, functions);
    }

    /// <summary>
    /// Creates a plugin from an array of agents. Each agent is converted into a KernelFunction via AgentKernelFunctionFactory.
    /// </summary>
    /// <param name="pluginName">The name for the plugin.</param>
    /// <param name="agents">The agents to include in the plugin.</param>
    /// <returns>A KernelPlugin with functions derived from the provided agents.</returns>
    public static KernelPlugin CreateFromAgents(string pluginName, params Agent[] agents) =>
        CreateFromAgents(pluginName, description: null, agents);
}
