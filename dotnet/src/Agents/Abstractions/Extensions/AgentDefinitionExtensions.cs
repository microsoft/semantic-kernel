// Copyright (c) Microsoft. All rights reserved.

using System.Linq;

namespace Microsoft.SemanticKernel.Agents;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
public static class AgentDefinitionExtensions
{
    /// <summary>
    /// Creates default <see cref="KernelArguments"/> from the <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition"></param>
    public static KernelArguments GetDefaultKernelArguments(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var arguments = new KernelArguments(agentDefinition?.Model?.Options);
        if (agentDefinition is not null)
        {
            // Add default arguments for the agent
            foreach (var input in agentDefinition.Inputs)
            {
                if (!input.IsRequired && input.Default is not null)
                {
                    arguments.Add(input.Name, input.Default);
                }
            }
        }

        return arguments;
    }

    /// <summary>
    /// Get the first tool definition of the specified type.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    /// <param name="toolType">Tool type</param>
    public static AgentToolDefinition? GetFirstToolDefinition(this AgentDefinition agentDefinition, string toolType)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(toolType);
        return agentDefinition.Tools?.FirstOrDefault(tool => tool.Type == toolType);
    }

    /// <summary>
    /// Determines if the agent definition has a code interpreter tool.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static bool IsEnableCodeInterpreter(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        return agentDefinition.Tools?.Where(tool => tool.Type == AgentToolDefinition.CodeInterpreter).Any() ?? false;
    }

    /// <summary>
    /// Determines if the agent definition has a file search tool.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static bool IsEnableFileSearch(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        return agentDefinition.Tools?.Where(tool => tool.Type == AgentToolDefinition.FileSearch).Any() ?? false;
    }
}
