// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Azure.AI.Projects;

namespace Microsoft.SemanticKernel.Agents.AzureAI;

/// <summary>
/// Provides extension methods for <see cref="AgentToolDefinition"/>.
/// </summary>
internal static class AgentToolDefinitionExtensions
{
    internal static AzureFunctionBinding GetInputBinding(this AgentToolDefinition agentToolDefinition)
    {
        return agentToolDefinition.GetAzureFunctionBinding("input_binding");
    }

    internal static AzureFunctionBinding GetOutputBinding(this AgentToolDefinition agentToolDefinition)
    {
        return agentToolDefinition.GetAzureFunctionBinding("output_binding");
    }

    internal static BinaryData GetParameters(this AgentToolDefinition agentToolDefinition)
    {
        var parameters = agentToolDefinition.GetOption<List<object>?>("parameters");
        return parameters is not null ? CreateParameterSpec(parameters) : s_noParams;
    }

    internal static BinaryData CreateParameterSpec(List<object> parameters)
    {
        JsonSchemaFunctionParameters parameterSpec = new();
        foreach (var parameter in parameters)
        {
            var parameterProps = parameter as Dictionary<object, object>;
            if (parameterProps is not null)
            {
                bool isRequired = parameterProps.TryGetValue("required", out var requiredValue) && requiredValue is string requiredString && requiredString.Equals("true", StringComparison.OrdinalIgnoreCase);
                string? name = parameterProps.TryGetValue("name", out var nameValue) && nameValue is string nameString ? nameString : null;
                string? type = parameterProps.TryGetValue("type", out var typeValue) && typeValue is string typeString ? typeString : null;
                string? description = parameterProps.TryGetValue("description", out var descriptionValue) && descriptionValue is string descriptionString ? descriptionString : string.Empty;

                if (string.IsNullOrEmpty(name) || string.IsNullOrEmpty(type))
                {
                    throw new ArgumentException("The option keys 'name' and 'type' are required for a parameter.");
                }

                if (isRequired)
                {
                    parameterSpec.Required.Add(name!);
                }
                parameterSpec.Properties.Add(name!, KernelJsonSchema.Parse($"{{ \"type\": \"{type}\", \"description\": \"{description}\" }}"));
            }
        }

        return BinaryData.FromObjectAsJson(parameterSpec);
    }

    internal static FileSearchToolDefinitionDetails GetFileSearchToolDefinitionDetails(this AgentToolDefinition agentToolDefinition)
    {
        var details = new FileSearchToolDefinitionDetails();
        var maxNumResults = agentToolDefinition.GetOption<int?>("max_num_results");
        if (maxNumResults is not null && maxNumResults > 0)
        {
            details.MaxNumResults = maxNumResults;
        }

        FileSearchRankingOptions? rankingOptions = agentToolDefinition.GetFileSearchRankingOptions();
        if (rankingOptions is not null)
        {
            details.RankingOptions = rankingOptions;
        }

        return details;
    }

    internal static ToolConnectionList GetToolConnectionList(this AgentToolDefinition agentToolDefinition)
    {
        Verify.NotNull(agentToolDefinition.Options);

        var toolConnections = agentToolDefinition.GetToolConnections();

        var toolConnectionList = new ToolConnectionList();
        if (toolConnections is not null)
        {
            toolConnectionList.ConnectionList.AddRange(toolConnections);
        }
        return toolConnectionList;
    }

    internal static BinaryData GetSpecification(this AgentToolDefinition agentToolDefinition)
    {
        Verify.NotNull(agentToolDefinition.Options);

        var specification = agentToolDefinition.GetRequiredOption<object>("specification");
        if (specification is string specificationStr)
        {
            return new BinaryData(specificationStr);
        }

        return new BinaryData(specification);
    }

    internal static OpenApiAuthDetails GetOpenApiAuthDetails(this AgentToolDefinition agentToolDefinition)
    {
        var connectionId = agentToolDefinition.GetOption<string>("connection_id");
        if (!string.IsNullOrEmpty(connectionId))
        {
            return new OpenApiConnectionAuthDetails(new OpenApiConnectionSecurityScheme(connectionId));
        }

        var audience = agentToolDefinition.GetOption<string>("audience");
        if (!string.IsNullOrEmpty(audience))
        {
            return new OpenApiManagedAuthDetails(new OpenApiManagedSecurityScheme(audience));
        }

        return new OpenApiAnonymousAuthDetails();
    }

    internal static List<string>? GetVectorStoreIds(this AgentToolDefinition agentToolDefinition)
    {
        return agentToolDefinition.GetOption<List<object>>("vector_store_ids")?.Select(id => id.ToString()!).ToList();
    }

    internal static List<string>? GetFileIds(this AgentToolDefinition agentToolDefinition)
    {
        return agentToolDefinition.GetOption<List<object>>("file_ids")?.Select(id => id.ToString()!).ToList();
    }

    internal static List<VectorStoreDataSource>? GetDataSources(this AgentToolDefinition agentToolDefinition)
    {
        var dataSources = agentToolDefinition.GetOption<List<object>?>("data_sources");
        return dataSources is not null ? CreateDataSources(dataSources) : null;
    }

    internal static List<VectorStoreDataSource> CreateDataSources(List<object> values)
    {
        List<VectorStoreDataSource> dataSources = [];
        foreach (var value in values)
        {
            if (value is Dictionary<object, object> dataSourceDict)
            {
                string? assetIdentifier = dataSourceDict.TryGetValue("asset_identifier", out var identifierValue) && identifierValue is string identifierString ? identifierString : null;
                string? assetType = dataSourceDict.TryGetValue("asset_type", out var typeValue) && typeValue is string typeString ? typeString : null;

                if (string.IsNullOrEmpty(assetIdentifier) || string.IsNullOrEmpty(assetType))
                {
                    throw new ArgumentException("The option keys 'asset_identifier' and 'asset_type' are required for a vector store data source.");
                }

                dataSources.Add(new VectorStoreDataSource(assetIdentifier, new VectorStoreDataSourceAssetType(assetType)));
            }
        }

        return dataSources;
    }

    internal static IList<VectorStoreConfigurations>? GetVectorStoreConfigurations(this AgentToolDefinition agentToolDefinition)
    {
        var dataSources = agentToolDefinition.GetOption<List<object>?>("configurations");
        return dataSources is not null ? CreateVectorStoreConfigurations(dataSources) : null;
    }

    internal static List<VectorStoreConfigurations> CreateVectorStoreConfigurations(List<object> values)
    {
        List<VectorStoreConfigurations> configurations = [];
        foreach (var value in values)
        {
            if (value is Dictionary<object, object> configurationDict)
            {
                var storeName = configurationDict.TryGetValue("store_name", out var storeNameValue) && storeNameValue is string storeNameString ? storeNameString : null;
                var dataSources = configurationDict.TryGetValue("data_sources", out var dataSourceValue) && dataSourceValue is List<object> dataSourceList ? CreateDataSources(dataSourceList) : null;

                if (string.IsNullOrEmpty(storeName) || dataSources is null)
                {
                    throw new ArgumentException("The option keys 'store_name' and 'data_sources' are required for a vector store configuration.");
                }

                configurations.Add(new VectorStoreConfigurations(storeName, new VectorStoreConfiguration(dataSources)));
            }
        }

        return configurations;
    }

    private static AzureFunctionBinding GetAzureFunctionBinding(this AgentToolDefinition agentToolDefinition, string bindingType)
    {
        Verify.NotNull(agentToolDefinition.Options);

        var binding = agentToolDefinition.GetRequiredOption<Dictionary<object, object>>(bindingType);
        if (!binding.TryGetValue("storage_service_endpoint", out var endpointValue) || endpointValue is not string storageServiceEndpoint)
        {
            throw new ArgumentException($"The option key '{bindingType}.storage_service_endpoint' is required.");
        }
        if (!binding.TryGetValue("queue_name", out var nameValue) || nameValue is not string queueName)
        {
            throw new ArgumentException($"The option key '{bindingType}.queue_name' is required.");
        }

        return new AzureFunctionBinding(new AzureFunctionStorageQueue(storageServiceEndpoint, queueName));
    }

    internal static int? GetTopK(this AgentToolDefinition agentToolDefinition)
    {
        return agentToolDefinition.Options?.TryGetValue("top_k", out var topKValue) ?? false
            ? int.Parse((string)topKValue!)
            : null;
    }

    internal static string? GetFilter(this AgentToolDefinition agentToolDefinition)
    {
        return agentToolDefinition.Options?.TryGetValue("filter", out var filterValue) ?? false
            ? filterValue as string
            : null;
    }

    internal static AzureAISearchQueryType? GetAzureAISearchQueryType(this AgentToolDefinition agentToolDefinition)
    {
        return agentToolDefinition.Options?.TryGetValue("query_type", out var queryTypeValue) ?? false
            ? new AzureAISearchQueryType(queryTypeValue as string)
            : null;
    }

    private static FileSearchRankingOptions? GetFileSearchRankingOptions(this AgentToolDefinition agentToolDefinition)
    {
        string? ranker = agentToolDefinition.GetOption<string>("ranker");
        float? scoreThreshold = agentToolDefinition.GetOption<float>("score_threshold");

        if (ranker is not null && scoreThreshold is not null)
        {
            return new FileSearchRankingOptions(ranker, (float)scoreThreshold!);
        }

        return null;
    }

    private static List<ToolConnection> GetToolConnections(this AgentToolDefinition agentToolDefinition)
    {
        Verify.NotNull(agentToolDefinition.Options);

        var toolConnections = agentToolDefinition.GetRequiredOption<List<object>>("tool_connections");

        return toolConnections.Select(connectionId => new ToolConnection(connectionId.ToString())).ToList();
    }

    private static T GetRequiredOption<T>(this AgentToolDefinition agentToolDefinition, string key)
    {
        Verify.NotNull(agentToolDefinition);
        Verify.NotNull(agentToolDefinition.Options);
        Verify.NotNull(key);

        if (agentToolDefinition.Options?.TryGetValue(key, out var value) ?? false)
        {
            if (value == null)
            {
                throw new ArgumentNullException($"The option key '{key}' must be a non null value.");
            }

            if (value is T expectedValue)
            {
                return expectedValue;
            }
            throw new InvalidCastException($"The option key '{key}' value must be of type '{typeof(T)}' but is '{value.GetType()}'.");
        }

        throw new ArgumentException($"The option key '{key}' was not found.");
    }

    private static readonly BinaryData s_noParams = BinaryData.FromObjectAsJson(new { type = "object", properties = new { } });
}
