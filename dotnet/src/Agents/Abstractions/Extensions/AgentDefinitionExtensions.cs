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
    /// <param name="agentDefinition">Agen definition to retrieve default arguments from.</param>
    public static KernelArguments GetDefaultKernelArguments(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var arguments = new KernelArguments(agentDefinition?.Model?.Options);
        if (agentDefinition is not null)
        {
            // Add default arguments for the agent
            foreach (var input in agentDefinition.Inputs)
            {
                if (input.Default is not null)
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
    /// <param name="agentDefinition">Agent definition to retrieve the first tool from.</param>
    /// <param name="toolType">Tool type</param>
    public static AgentToolDefinition? GetFirstToolDefinition(this AgentDefinition agentDefinition, string toolType)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(toolType);
        return agentDefinition.Tools?.FirstOrDefault(tool => tool.Type == toolType);
    }

    /// <summary>
    /// Determines if the agent definition has a tool of the specified type.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    /// <param name="toolType">Tool type</param>
    public static bool HasToolType(this AgentDefinition agentDefinition, string toolType)
    {
        Verify.NotNull(agentDefinition);

        return agentDefinition.Tools?.Any(tool => tool?.Type?.Equals(toolType, System.StringComparison.Ordinal) ?? false) ?? false;
    }
}
