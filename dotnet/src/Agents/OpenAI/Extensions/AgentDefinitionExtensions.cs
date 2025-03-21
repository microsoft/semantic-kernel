// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using Azure.AI.OpenAI;
using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Http;
using OpenAI;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class AgentDefinitionExtensions
{
    private const string CodeInterpreterType = "code_interpreter";
    private const string FileSearchType = "file_search";

    private const string FileIds = "file_ids";
    private const string ApiKey = "api_key";
    private const string OpenAI = "openai";
    private const string AzureOpenAI = "azure_openai";

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
            Temperature = agentDefinition.GetTemperature(),
            NucleusSamplingFactor = agentDefinition.GetTopP(),
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
                    case CodeInterpreterType:
                        assistantCreationOptions.Tools.Add(ToolDefinition.CreateCodeInterpreter());
                        break;
                    case FileSearchType:
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

        var toolDefinition = agentDefinition.GetFirstToolDefinition(CodeInterpreterType);
        if ((toolDefinition?.Options?.TryGetValue(FileIds, out var value) ?? false) && value is List<string> fileIds)
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

    /// <summary>
    /// Return the <see cref="OpenAIClient"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition which will be used to provide connection for the <see cref="OpenAIClient"/>.</param>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="OpenAIClient"/>.</param>
    public static OpenAIClient GetOpenAIClient(this AgentDefinition agentDefinition, Kernel kernel)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent connection as the first option
        var connection = agentDefinition?.Model?.Connection;
        if (connection is not null)
        {
            if (connection.Type is null)
            {
                throw new InvalidOperationException("Model connection type must be specified.");
            }

#pragma warning disable CA2000 // Dispose objects before losing scope, not applicable because the HttpClient is created and may be used elsewhere
            var httpClient = HttpClientProvider.GetHttpClient(kernel.Services);
#pragma warning restore CA2000 // Dispose objects before losing scope

            if (connection.Type.Equals(OpenAI, StringComparison.OrdinalIgnoreCase))
            {
                OpenAIClientOptions clientOptions = OpenAIClientProvider.CreateOpenAIClientOptions(connection.TryGetEndpoint(), httpClient);
                return new OpenAIClient(connection.GetApiKeyCredential(), clientOptions);
            }
            else if (connection.Type.Equals(AzureOpenAI, StringComparison.OrdinalIgnoreCase))
            {
                var endpoint = connection.TryGetEndpoint();
                Verify.NotNull(endpoint, "Endpoint must be specified when using Azure OpenAI.");

                AzureOpenAIClientOptions clientOptions = OpenAIClientProvider.CreateAzureClientOptions(httpClient);
                if (connection.ExtensionData.TryGetValue(ApiKey, out var apiKey) && apiKey is not null)
                {
                    return new AzureOpenAIClient(endpoint, connection.GetApiKeyCredential(), clientOptions);
                }

                var tokenCredential = kernel.Services.GetRequiredService<TokenCredential>();
                return new AzureOpenAIClient(endpoint, tokenCredential, clientOptions);
            }

            throw new InvalidOperationException($"Invalid OpenAI client type '{connection.Type}' was specified.");
        }

        // Use the client registered on the kernel
        var client = kernel.GetAllServices<OpenAIClient>().FirstOrDefault();
        return (OpenAIClient?)client ?? throw new InvalidOperationException("OpenAI client not found.");
    }

    #region private
    private const string Temperature = "temperature";
    private const string TopP = "top_p";

    private static float? GetTemperature(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        if (agentDefinition?.Model?.Options?.TryGetValue(Temperature, out var temperature) ?? false)
        {
            return (float?)temperature;
        }
        return null;
    }

    private static float? GetTopP(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        if (agentDefinition?.Model?.Options?.TryGetValue(TopP, out var topP) ?? false)
        {
            return (float?)topP;
        }
        return null;
    }
    #endregion
}
