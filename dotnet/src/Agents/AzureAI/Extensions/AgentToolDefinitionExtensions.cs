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
