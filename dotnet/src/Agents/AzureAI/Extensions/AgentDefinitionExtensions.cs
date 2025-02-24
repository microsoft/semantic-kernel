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
    private const string AzureAISearchType = "azure_aisearch";
    private const string AzureFunctionType = "azure_function";
    private const string BingGroundingType = "bing_grounding";
    private const string CodeInterpreterType = "code_interpreter";
    private const string FileSearchType = "file_search";
    private const string FunctionToolType = "function_tool";
    private const string MicrosoftFabricType = "microsoft_fabric";
    private const string OpenApiType = "openapi";
    private const string SharepointType = "sharepoint";

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
                AzureAISearchType => CreateAzureAISearchToolDefinition(tool),
                AzureFunctionType => CreateAzureFunctionToolDefinition(tool),
                BingGroundingType => CreateBingGroundingToolDefinition(tool),
                CodeInterpreterType => CreateCodeInterpreterToolDefinition(tool),
                FileSearchType => CreateFileSearchToolDefinition(tool),
                FunctionToolType => CreateFunctionToolDefinition(tool),
                MicrosoftFabricType => CreateMicrosoftFabricToolDefinition(tool),
                OpenApiType => CreateOpenApiToolDefinition(tool),
                SharepointType => CreateSharepointToolDefinition(tool),
                _ => throw new InvalidOperationException($"Unable to created Azure AI tool definition because of known tool type: {tool.Type}"),
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

    #region private
    private static AzureAISearchToolDefinition CreateAzureAISearchToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);

        return new AzureAISearchToolDefinition();
    }

    private static AzureFunctionToolDefinition CreateAzureFunctionToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);
        Verify.NotNull(tool.Name);
        Verify.NotNull(tool.Description);

        string name = tool.Name;
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
        Verify.NotNull(tool.Name);
        Verify.NotNull(tool.Description);

        string name = tool.Name;
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
        Verify.NotNull(tool.Name);
        Verify.NotNull(tool.Description);

        string name = tool.Name;
        string description = tool.Description;
        BinaryData spec = tool.GetSpecification();
        OpenApiAuthDetails auth = tool.GetOpenApiAuthDetails();

        return new OpenApiToolDefinition(name, description, spec, auth);
    }

    private static SharepointToolDefinition CreateSharepointToolDefinition(AgentToolDefinition tool)
    {
        Verify.NotNull(tool);

        ToolConnectionList sharepointGrounding = tool.GetToolConnectionList();

        return new SharepointToolDefinition(sharepointGrounding);
    }
    #endregion
}
