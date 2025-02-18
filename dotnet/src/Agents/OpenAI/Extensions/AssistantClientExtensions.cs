// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Agents.OpenAI.Internal;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Convenience extensions for <see cref="AssistantClient"/>.
/// </summary>
public static class AssistantClientExtensions
{
    /// <summary>
    /// Creates an assistant asynchronously with the specified options.
    /// </summary>
    /// <param name="client">The assistant client.</param>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="name">The name of the assistant.</param>
    /// <param name="description">The description of the assistant.</param>
    /// <param name="instructions">The instructions for the assistant.</param>
    /// <param name="enableCodeInterpreter">Whether to enable the code interpreter tool.</param>
    /// <param name="codeInterpreterFileIds">The file IDs for the code interpreter tool.</param>
    /// <param name="enableFileSearch">Whether to enable the file search tool.</param>
    /// <param name="vectorStoreId">The vector store identifier.</param>
    /// <param name="temperature">The temperature setting for the assistant.</param>
    /// <param name="topP">The nucleus sampling factor for the assistant.</param>
    /// <param name="responseFormat">The response format for the assistant.</param>
    /// <param name="metadata">The metadata for the assistant.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created assistant.</returns>
    public static async Task<Assistant> CreateAssistantAsync(
        this AssistantClient client,
        string modelId,
        string? name = null,
        string? description = null,
        string? instructions = null,
        bool enableCodeInterpreter = false,
        IReadOnlyList<string>? codeInterpreterFileIds = null,
        bool enableFileSearch = false,
        string? vectorStoreId = null,
        float? temperature = null,
        float? topP = null,
        AssistantResponseFormat? responseFormat = null,
        IReadOnlyDictionary<string, string>? metadata = null,
        CancellationToken cancellationToken = default)
    {
        AssistantCreationOptions options =
            new()
            {
                Name = name,
                Description = description,
                Instructions = instructions,
                Temperature = temperature,
                NucleusSamplingFactor = topP,
                ResponseFormat = responseFormat,
            };

        if (metadata != null)
        {
            foreach (KeyValuePair<string, string> item in metadata)
            {
                options.Metadata[item.Key] = item.Value;
            }
        }

        if (enableCodeInterpreter || (codeInterpreterFileIds?.Count ?? 0) > 0)
        {
            options.Tools.Add(ToolDefinition.CreateCodeInterpreter());
        }

        if (enableFileSearch || !string.IsNullOrEmpty(vectorStoreId))
        {
            options.Tools.Add(ToolDefinition.CreateFileSearch());
        }

        options.ToolResources = AssistantToolResourcesFactory.GenerateToolResources(vectorStoreId, codeInterpreterFileIds);

        Assistant assistant = await client.CreateAssistantAsync(modelId, options, cancellationToken).ConfigureAwait(false);

        return assistant;
    }

    /// <summary>
    /// Creates an assistant from a template asynchronously with the specified options.
    /// </summary>
    /// <param name="client">The assistant client.</param>
    /// <param name="modelId">The model identifier.</param>
    /// <param name="config">The prompt template configuration.</param>
    /// <param name="enableCodeInterpreter">Whether to enable the code interpreter tool.</param>
    /// <param name="codeInterpreterFileIds">The file IDs for the code interpreter tool.</param>
    /// <param name="enableFileSearch">Whether to enable the file search tool.</param>
    /// <param name="vectorStoreId">The vector store identifier.</param>
    /// <param name="temperature">The temperature setting for the assistant.</param>
    /// <param name="topP">The nucleus sampling factor for the assistant.</param>
    /// <param name="responseFormat">The response format for the assistant.</param>
    /// <param name="metadata">The metadata for the assistant.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the created assistant.</returns>
    public static Task<Assistant> CreateAssistantFromTemplateAsync(
        this AssistantClient client,
        string modelId,
        PromptTemplateConfig config,
        bool enableCodeInterpreter = false,
        IReadOnlyList<string>? codeInterpreterFileIds = null,
        bool enableFileSearch = false,
        string? vectorStoreId = null,
        float? temperature = null,
        float? topP = null,
        AssistantResponseFormat? responseFormat = null,
        IReadOnlyDictionary<string, string>? metadata = null,
        CancellationToken cancellationToken = default)
    {
        return
            client.CreateAssistantAsync(
                modelId,
                config.Name,
                config.Description,
                config.Template,
                enableCodeInterpreter,
                codeInterpreterFileIds,
                enableFileSearch,
                vectorStoreId,
                temperature,
                topP,
                responseFormat,
                metadata,
                cancellationToken);
    }

    /// <summary>
    /// Creates a thread asynchronously with the specified options.
    /// </summary>
    /// <param name="client">The assistant client.</param>
    /// <param name="messages">The initial messages for the thread.</param>
    /// <param name="codeInterpreterFileIds">The file IDs for the code interpreter tool.</param>
    /// <param name="vectorStoreId">The vector store identifier.</param>
    /// <param name="metadata">The metadata for the thread.</param>
    /// <param name="cancellationToken">The cancellation token.</param>
    /// <returns>A task that represents the asynchronous operation. The task result contains the thread ID.</returns>
    public static async Task<string> CreateThreadAsync(
        this AssistantClient client,
        IEnumerable<ChatMessageContent>? messages = null,
        IReadOnlyList<string>? codeInterpreterFileIds = null,
        string? vectorStoreId = null,
        IReadOnlyDictionary<string, string>? metadata = null,
        CancellationToken cancellationToken = default)
    {
        ThreadCreationOptions options = new()
        {
            ToolResources = AssistantToolResourcesFactory.GenerateToolResources(vectorStoreId, codeInterpreterFileIds)
        };

        if (messages != null)
        {
            options.InitialMessages.AddRange(messages.ToThreadInitializationMessages());
        }

        if (metadata != null)
        {
            foreach (KeyValuePair<string, string> item in metadata)
            {
                options.Metadata[item.Key] = item.Value;
            }
        }

        AssistantThread thread = await client.CreateThreadAsync(options, cancellationToken).ConfigureAwait(false);

        return thread.Id;
    }
}
