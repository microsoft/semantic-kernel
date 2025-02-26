// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
internal static class AgentDefinitionExtensions
{
    /// <summary>
    /// Return the Azure AI tool definitions which corresponds with the provided <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    /// <exception cref="InvalidOperationException"></exception>
    public static IEnumerable<ToolDefinition> GetAzureToolDefinitions(this AgentDefinition agentDefinition)
    {
        return agentDefinition.Tools.Select<AgentToolDefinition, ToolDefinition>(tool =>
        {
            return tool.Type switch
            {
                "code_interpreter" => new CodeInterpreterToolDefinition(),
                "file_search" => new FileSearchToolDefinition(),
                _ => throw new NotSupportedException($"Unable to create Azure AI tool definition because of unsupported tool type: {tool.Type}"),
            };
        });
    }

    /// <summary>
    /// Retrieve the metadata from the agent definition.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static IReadOnlyDictionary<string, string>? GetMetadata(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        // TODO: Implement
        return null;
    }
}
