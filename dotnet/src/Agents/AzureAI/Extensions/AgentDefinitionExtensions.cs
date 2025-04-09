// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.Projects;
using Azure.Core;
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
    private const string MicrosoftFabricType = "fabric_aiskill";
    private const string OpenApiType = "openapi";
    private const string SharepointGroundingType = "sharepoint_grounding";

    private static readonly string[] s_validToolTypes = new string[]
    {
        AzureAISearchType,
        AzureFunctionType,
        BingGroundingType,
        CodeInterpreterType,
        FileSearchType,
        FunctionType,
        MicrosoftFabricType,
        OpenApiType,
        SharepointGroundingType
    };

    private const string ConnectionString = "connection_string";

    /// <summary>
    /// Return the Azure AI tool definitions which corresponds with the provided <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition</param>
    /// <exception cref="InvalidOperationException"></exception>
    public static IEnumerable<ToolDefinition> GetAzureToolDefinitions(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        return agentDefinition.Tools?.Select<AgentToolDefinition, ToolDefinition>(tool =>
        {
            return tool.Type switch
            {
                AzureAISearchType => CreateAzureAISearchToolDefinition(tool),
                AzureFunctionType => CreateAzureFunctionToolDefinition(tool),
                BingGroundingType => CreateBingGroundingToolDefinition(tool),
                CodeInterpreterType => CreateCodeInterpreterToolDefinition(tool),
                FileSearchType => CreateFileSearchToolDefinition(tool),
                FunctionType => CreateFunctionToolDefinition(tool),
                MicrosoftFabricType => CreateMicrosoftFabricToolDefinition(tool),
                OpenApiType => CreateOpenApiToolDefinition(tool),
                SharepointGroundingType => CreateSharepointGroundingToolDefinition(tool),
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
    /// Return the <see cref="AIProjectClient"/> to be used with the specified <see cref="AgentDefinition"/>.
    /// </summary>
    /// <param name="agentDefinition">Agent definition which will be used to provide connection for the <see cref="AIProjectClient"/>.</param>
    /// <param name="kernel">Kernel instance which will be used to resolve a default <see cref="AIProjectClient"/>.</param>
    public static AIProjectClient GetAIProjectClient(this AgentDefinition agentDefinition, Kernel kernel)
    {
        Verify.NotNull(agentDefinition);

        // Use the agent connection as the first option
        var connection = agentDefinition?.Model?.Connection;
        if (connection is not null)
        {
            if (connection.ExtensionData.TryGetValue(ConnectionString, out var value) && value is string connectionString)
            {
#pragma warning disable CA2000 // Dispose objects before losing scope, not relevant because the HttpClient is created and may be used elsewhere
                var httpClient = HttpClientProvider.GetHttpClient(kernel.Services);
#pragma warning restore CA2000 // Dispose objects before losing scope
                AIProjectClientOptions clientOptions = AzureAIClientProvider.CreateAzureClientOptions(httpClient);

                var tokenCredential = kernel.Services.GetRequiredService<TokenCredential>();
                return new(connectionString, tokenCredential, clientOptions);
            }
        }

        // Return the client registered on the kernel
        var client = kernel.GetAllServices<AIProjectClient>().FirstOrDefault();
        return (AIProjectClient?)client ?? throw new InvalidOperationException("AzureAI project client not found.");
    }

    #region private
    private static CodeInterpreterToolResource? GetCodeInterpreterToolResource(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);
        return null;
    }

    private static FileSearchToolResource? GetFileSearchToolResource(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);

        var fileSearch = agentDefinition.GetFirstToolDefinition(FileSearchType);
        if (fileSearch is not null)
        {
            var vectorStoreIds = fileSearch.GetVectorStoreIds();
            if (vectorStoreIds is not null)
            {
                return new FileSearchToolResource(vectorStoreIds, vectorStores: null);
            }
        }

        return null;
    }

    private static AzureAISearchResource? GetAzureAISearchResource(this AgentDefinition agentDefinition)
    {
        Verify.NotNull(agentDefinition);
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

    private static BingGroundingToolDefinition CreateBingGroundingToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);

        ToolConnectionList bingGrounding = tool.GetToolConnectionList();

        return new BingGroundingToolDefinition(bingGrounding);
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

    private static MicrosoftFabricToolDefinition CreateMicrosoftFabricToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);

        ToolConnectionList fabricAiskill = tool.GetToolConnectionList();

        return new MicrosoftFabricToolDefinition(fabricAiskill);
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

    private static SharepointToolDefinition CreateSharepointGroundingToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);

        ToolConnectionList sharepointGrounding = tool.GetToolConnectionList();

        return new SharepointToolDefinition(sharepointGrounding);
    }
    #endregion
}
