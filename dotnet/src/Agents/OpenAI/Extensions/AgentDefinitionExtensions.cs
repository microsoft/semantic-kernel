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
    /// Property name for the file ids configuration.
    /// </summary>
    public const string FileIds = "file_ids";

    /// <summary>
    /// Create the <see cref="AssistantCreationOptions"/> which corresponds with the provided <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static AssistantCreationOptions CreateAssistantCreationOptions(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Model);
        Verify.NotNull(agentDefinition.Model.Id);

        var assistantCreationOptions = new AssistantCreationOptions()
        {
            Name = agentDefinition.Name,
            Description = agentDefinition.Description,
            Instructions = agentDefinition.Instructions,
            Temperature = agentDefinition?.Model?.Options?.GetTemperature(),
            NucleusSamplingFactor = agentDefinition?.Model?.Options?.GetTopP(),
            ResponseFormat = agentDefinition?.Model?.Options?.IsEnableJsonResponse() ?? false ? AssistantResponseFormat.JsonObject : AssistantResponseFormat.Auto
        };

        // TODO: Implement
        // ToolResources
        // Metadata
        // ExecutionOptions

        if (agentDefinition?.IsEnableCodeInterpreter() ?? false)
        {
            assistantCreationOptions.Tools.Add(ToolDefinition.CreateCodeInterpreter());
        }

        if (agentDefinition?.IsEnableFileSearch() ?? false)
        {
            assistantCreationOptions.Tools.Add(ToolDefinition.CreateFileSearch());
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

        var toolDefinition = agentDefinition.GetFirstToolDefinition(AgentToolDefinition.CodeInterpreter);
        if (toolDefinition?.Configuration?.TryGetValue(FileIds, out var fileIds) ?? false)
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
