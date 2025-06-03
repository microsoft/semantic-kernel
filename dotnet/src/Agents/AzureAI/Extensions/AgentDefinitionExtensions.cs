// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Azure.AI.Agents.Persistent;
using Azure.AI.Projects;
using Azure.Core;
using Azure.Core.Pipeline;
using Azure.Identity;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides extension methods for <see cref="AgentDefinition"/>.
/// </summary>
internal static class AgentDefinitionExtensions
{
    private const string AzureAISearchType = "azure_ai_search";
    private const string AzureFunctionType = "azure_function";
    private const string BingGroundingType = "bing_grounding";
    private const string CodeInterpreterType = "code_interpreter";
    private const string FileSearchType = "file_search";
    private const string FunctionType = "function";
    private const string OpenApiType = "openapi";

    private static readonly string[] s_validToolTypes =
    [
        AzureAISearchType,
        AzureFunctionType,
        BingGroundingType,
        CodeInterpreterType,
        FileSearchType,
        FunctionType,
        OpenApiType,
    ];

    private const string Endpoint = "endpoint";

    /// <summary>
    /// Return the Azure AI tool definitions which corresponds with the provided <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    /// <param name="kernel">Kernel instance to associate with the agent.</param>
    /// <exception cref="InvalidOperationException"></exception>
    public static IEnumerable<ToolDefinition> GetAzureToolDefinitions(this AgentDefinition agentDefinition, Kernel kernel)
    {
        Verify.NotNull(agentDefinition);

        AIProjectClient projectClient = agentDefinition.GetProjectsClient(kernel);

        return agentDefinition.Tools?.Select<AgentToolDefinition, ToolDefinition>(tool =>
        {
            return tool.Type switch
            {
                AzureAISearchType => CreateAzureAISearchToolDefinition(tool),
                AzureFunctionType => CreateAzureFunctionToolDefinition(tool),
                BingGroundingType => CreateBingGroundingToolDefinition(tool, projectClient),
                CodeInterpreterType => CreateCodeInterpreterToolDefinition(tool),
                FileSearchType => CreateFileSearchToolDefinition(tool),
                FunctionType => CreateFunctionToolDefinition(tool),
                OpenApiType => CreateOpenApiToolDefinition(tool),
                _ => throw new NotSupportedException($"Unable to create Azure AI tool definition because of unsupported tool type: {tool.Type}, supported tool types are: {string.Join(",", s_validToolTypes)}"),
            };
        }) ?? [];
    }

    /// <summary>
    /// Return the Azure AI tool resources which corresponds with the provided <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    public static ToolResources GetAzureToolResources(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var toolResources = new ToolResources();

        var codeInterpreter = agentDefinition.GetCodeInterpreterToolResource();
        if (codeInterpreter is not null)
        {
            toolResources.CodeInterpreter = codeInterpreter;
        }
        var fileSearch = agentDefinition.GetFileSearchToolResource();
        if (fileSearch is not null)
        {
            toolResources.FileSearch = fileSearch;
        }
        var azureAISearch = agentDefinition.GetAzureAISearchResource();
        if (azureAISearch is not null)
        {
            toolResources.AzureAISearch = azureAISearch;
        }

        return toolResources;
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
    /// Return the <see cref="PersistentAgentsClient"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition which will be used to provide connection for the <see cref="PersistentAgentsClient"/>.</param>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="PersistentAgentsClient"/>.</param>
    public static PersistentAgentsClient GetAgentsClient(this AgentDefinition agentDefinition, Kernel kernel)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent connection as the first option
        var connection = agentDefinition?.Model?.Connection;
        if (connection is not null)
        {
            if (connection.ExtensionData.TryGetValue(Endpoint, out var value) && value is string endpoint)
            {
#pragma warning disable CA2000 // Dispose objects before losing scope, not relevant because the HttpClient is created and may be used elsewhere
                var httpClient = HttpClientProvider.GetHttpClient(kernel.Services);
#pragma warning restore CA2000 // Dispose objects before losing scope

                var tokenCredential = kernel.Services.GetRequiredService<TokenCredential>();
                return AzureAIAgent.CreateAgentsClient(endpoint, tokenCredential, httpClient);
            }
        }

        // Return the client registered on the kernel
        var client = kernel.GetAllServices<PersistentAgentsClient>().FirstOrDefault();
        return client ?? throw new InvalidOperationException("AzureAI agents client not found.");
    }

    /// <summary>
    /// Return the <see cref="PersistentAgentsClient"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition which will be used to provide connection for the <see cref="PersistentAgentsClient"/>.</param>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="PersistentAgentsClient"/>.</param>
    public static AIProjectClient GetProjectsClient(this AgentDefinition agentDefinition, Kernel kernel)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent connection as the first option
        var connection = agentDefinition?.Model?.Connection;
        if (connection is not null)
        {
            if (connection.ExtensionData.TryGetValue(Endpoint, out var value) && value is string endpoint)
            {
#pragma warning disable CA2000 // Dispose objects before losing scope, not relevant because the HttpClient is created and may be used elsewhere
                var httpClient = HttpClientProvider.GetHttpClient(kernel.Services);
#pragma warning restore CA2000 // Dispose objects before losing scope

                var tokenCredential = kernel.Services.GetRequiredService<TokenCredential>();
                AIProjectClientOptions options =
                    new()
                    {
                        Transport = new HttpClientTransport(httpClient),
                        RetryPolicy = new RetryPolicy(maxRetries: 0) // Disable retry policy if a custom HttpClient is provided.
                    };
                return new AIProjectClient(new Uri(endpoint), tokenCredential, options);
            }
        }

        // Return the client registered on the kernel
        var client = kernel.GetAllServices<AIProjectClient>().FirstOrDefault();
        return client ?? throw new InvalidOperationException("AzureAI project client not found.");
    }

    #region private
    private static CodeInterpreterToolResource? GetCodeInterpreterToolResource(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        CodeInterpreterToolResource? resource = null;

        var codeInterpreter = agentDefinition.GetFirstToolDefinition(CodeInterpreterType);
        if (codeInterpreter is not null)
        {
            var fileIds = codeInterpreter.GetFileIds();
            var dataSources = codeInterpreter.GetDataSources();
            if (fileIds is not null || dataSources is not null)
            {
                resource = new CodeInterpreterToolResource();
                if (fileIds is not null)
                {
                    resource.FileIds.AddRange(fileIds);
                }
                if (dataSources is not null)
                {
                    resource.DataSources.AddRange(dataSources);
                }
            }
        }

        return resource;
    }

    private static FileSearchToolResource? GetFileSearchToolResource(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var fileSearch = agentDefinition.GetFirstToolDefinition(FileSearchType);
        if (fileSearch is not null)
        {
            var vectorStoreIds = fileSearch.GetVectorStoreIds();
            var vectorStores = fileSearch.GetVectorStoreConfigurations();
            if (vectorStoreIds is not null || vectorStores is not null)
            {
                return new FileSearchToolResource(vectorStoreIds, vectorStores);
            }
        }

        return null;
    }

    private static AzureAISearchToolResource? GetAzureAISearchResource(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var azureAISearch = agentDefinition.GetFirstToolDefinition(AzureAISearchType);
        if (azureAISearch is not null)
        {
            string? indexConnectionId = azureAISearch.GetOption<string>("index_connection_id");
            string? indexName = azureAISearch.GetOption<string>("index_name");
            if (string.IsNullOrEmpty(indexConnectionId) && string.IsNullOrEmpty(indexName))
            {
                return null;
            }
            if (string.IsNullOrEmpty(indexConnectionId) || string.IsNullOrEmpty(indexName))
            {
                throw new InvalidOperationException("Azure AI Search tool definition must have both 'index_connection_id' and 'index_name' options set.");
            }
            int topK = azureAISearch.GetTopK() ?? 5;
            string filter = azureAISearch.GetFilter() ?? string.Empty;
            AzureAISearchQueryType? queryType = azureAISearch.GetAzureAISearchQueryType();

            return new AzureAISearchToolResource(indexConnectionId, indexName, topK, filter, queryType);
        }

        return null;
    }

    private static AzureAISearchToolDefinition CreateAzureAISearchToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);

        return new AzureAISearchToolDefinition();
    }

    private static AzureFunctionToolDefinition CreateAzureFunctionToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);
        Verify.NotNull(tool.Id);
        Verify.NotNull(tool.Description);

        string name = tool.Id;
        string description = tool.Description;
        AzureFunctionBinding inputBinding = tool.GetInputBinding();
        AzureFunctionBinding outputBinding = tool.GetOutputBinding();
        BinaryData parameters = tool.GetParameters();

        return new AzureFunctionToolDefinition(name, description, inputBinding, outputBinding, parameters);
    }

    private static BingGroundingToolDefinition CreateBingGroundingToolDefinition(AgentToolDefinition tool, AIProjectClient projectClient)
    {
        Verify.NotNull(tool);

        IEnumerable<string> connectionIds = projectClient.GetConnectionIds(tool);
        BingGroundingSearchToolParameters bingToolParameters = new([new BingGroundingSearchConfiguration(connectionIds.Single())]);

        return new BingGroundingToolDefinition(bingToolParameters);
    }

    private static CodeInterpreterToolDefinition CreateCodeInterpreterToolDefinition(AgentToolDefinition tool)
    {
        return new CodeInterpreterToolDefinition();
    }

    private static FileSearchToolDefinition CreateFileSearchToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);

        return new FileSearchToolDefinition()
        {
            FileSearch = tool.GetFileSearchToolDefinitionDetails()
        };
    }

    private static FunctionToolDefinition CreateFunctionToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);
        Verify.NotNull(tool.Id);
        Verify.NotNull(tool.Description);

        string name = tool.Id;
        string description = tool.Description;
        BinaryData parameters = tool.GetParameters();

        return new FunctionToolDefinition(name, description, parameters);
    }

    private static OpenApiToolDefinition CreateOpenApiToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);
        Verify.NotNull(tool.Id);
        Verify.NotNull(tool.Description);

        string name = tool.Id;
        string description = tool.Description;
        BinaryData spec = tool.GetSpecification();
        OpenApiAuthDetails auth = tool.GetOpenApiAuthDetails();

        return new OpenApiToolDefinition(name, description, spec, auth);
    }

    private static IEnumerable<string> GetConnectionIds(this AIProjectClient projectClient, AgentToolDefinition tool)
    {
        HashSet<string> connections = [.. tool.GetToolConnections()];
        Connections connectionClient = projectClient.GetConnectionsClient();
        return
            connectionClient.GetConnections()
                .Where(connection => connections.Contains(connection.Name))
                .Select(connection => connection.Id);
    }
    #endregion
}
