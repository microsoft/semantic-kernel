// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class AgentDefinitionExtensions
{
    /// <summary>
    /// Tool definition type for code interpreter.
    /// </summary>
    internal const string CodeInterpreter = "code_interpreter";

    /// <summary>
    /// Tool definition type for file search.
    /// </summary>
    internal const string FileSearch = "file_search";

    /// <summary>
    /// Property name for the file ids configuration.
    /// </summary>
    internal const string FileIds = "file_ids";

    /// <summary>
    /// Create the <see cref="AssistantCreationOptions"/> which corresponds with the provided <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static AssistantCreationOptions CreateAssistantCreationOptions(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Model, nameof(agentDefinition.Model));
        Verify.NotNull(agentDefinition.Model.Id, nameof(agentDefinition.Model.Id));

        var assistantCreationOptions = new AssistantCreationOptions()
        {
            Name = agentDefinition.Name,
            Description = agentDefinition.Description,
            Instructions = agentDefinition.Instructions,
            Temperature = agentDefinition.Model.Options?.GetTemperature(),
            NucleusSamplingFactor = agentDefinition.Model.Options?.GetTopP(),
        };

        // TODO: Implement
        // ResponseFormat
        // ToolResources
        // Metadata
        // ExecutionOptions

        // Add tools
        if (agentDefinition.Tools is not null)
        {
            foreach (var tool in agentDefinition.Tools)
            {
                switch (tool.Type)
                {
                    case CodeInterpreter:
                        assistantCreationOptions.Tools.Add(ToolDefinition.CreateCodeInterpreter());
                        break;
                    case FileSearch:
                        assistantCreationOptions.Tools.Add(ToolDefinition.CreateFileSearch());
                        break;
                    default:
                        throw new System.NotSupportedException($"Tool type '{tool.Type}' is not supported.");
                }
            }
        }

        return assistantCreationOptions;
    }

    /// <summary>
    /// Retrieve the code interpreter file IDs from the agent definition.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static IReadOnlyList<string>? GetCodeInterpreterFileIds(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var toolDefinition = agentDefinition.GetFirstToolDefinition(CodeInterpreter);
        if ((toolDefinition?.Configuration?.TryGetValue(FileIds, out var value) ?? false) && value is List<string> fileIds)
        {
            // TODO: Verify that the fileIds are strings
            return (IReadOnlyList<string>)fileIds;
        }

        return null;
    }

    /// <summary>
    /// Retrieve the vector store ID from the agent definition.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static string? GetVectorStoreId(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        // TODO: Implement
        return null;
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
