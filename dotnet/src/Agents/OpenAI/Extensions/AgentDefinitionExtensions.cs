// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
internal static class AgentDefinitionExtensions
{
    /// <summary>
    /// Property name for the file ids configuration.
    /// </summary>
    public const string FileIds = "file_ids";

    /// <summary>
    /// Return the <see cref="OpenAIAssistantDefinition"/> which corresponds with the provided <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static OpenAIAssistantDefinition GetOpenAIAssistantDefinition(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);
        Verify.NotNull(agentDefinition.Model);
        Verify.NotNull(agentDefinition.Model.Id);

        return new OpenAIAssistantDefinition(agentDefinition.Model.Id)
        {
            Id = agentDefinition.Id ?? string.Empty,
            Name = agentDefinition.Name,
            Description = agentDefinition.Description,
            Instructions = agentDefinition.Instructions,
            EnableCodeInterpreter = agentDefinition.IsEnableCodeInterpreter(),
            CodeInterpreterFileIds = agentDefinition.GetCodeInterpreterFileIds(),
            EnableFileSearch = agentDefinition.IsEnableFileSearch(),
            VectorStoreId = agentDefinition.GetVectorStoreId(),
            EnableJsonResponse = agentDefinition?.Model?.Options?.IsEnableJsonResponse() ?? false,
            Temperature = agentDefinition?.Model?.Options?.GetTemperature(),
            TopP = agentDefinition?.Model?.Options?.GetTopP(),
            ExecutionOptions = agentDefinition?.GetExecutionOptions(),
            Metadata = agentDefinition?.GetMetadata(),
        };
    }

    /// <summary>
    /// Retrieve the code interpreter file IDs from the agent definition.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static IReadOnlyList<string>? GetCodeInterpreterFileIds(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var toolDefinition = agentDefinition.GetFirstToolDefinition(ToolDefinition.CodeInterpreter);
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
    /// Retrieve the execution options from the agent definition.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static OpenAIAssistantExecutionOptions? GetExecutionOptions(this AgentDefinition agentDefinition)
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
