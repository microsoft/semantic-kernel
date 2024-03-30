// Copyright (c) Microsoft. All rights reserved.
namespace Microsoft.SemanticKernel.Experimental.Agents;

/// <summary>
/// Extension methods for <see cref="KernelAgent"/>
/// </summary>
public static class AgentExtensions
{
    /// <summary>
    /// $$$
    /// </summary>
    /// <param name="agent"></param>
    /// <returns></returns>
    public static NexusPlugin AsPlugin(this Agent agent)
    {
        return new NexusPlugin(agent);
    }
}
