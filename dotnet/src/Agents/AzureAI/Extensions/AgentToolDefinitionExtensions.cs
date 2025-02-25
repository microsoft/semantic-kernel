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
        Verify.NotNull(agentToolDefinition.Configuration);

        var parameters = agentToolDefinition.GetConfiguration<List<object>>("parameters");

        // TODO Needswork
        return parameters is not null ? new BinaryData(parameters) : s_noParams;
    }

    internal static FileSearchToolDefinitionDetails GetFileSearchToolDefinitionDetails(this AgentToolDefinition agentToolDefinition)
    {
        var details = new FileSearchToolDefinitionDetails()
        {
            MaxNumResults = agentToolDefinition.GetConfiguration<int>("max_num_results")
        };

        FileSearchRankingOptions? rankingOptions = agentToolDefinition.GetFileSearchRankingOptions();
        if (rankingOptions is not null)
        {
            details.RankingOptions = rankingOptions;
        }

        return details;
    }

    internal static ToolConnectionList GetToolConnectionList(this AgentToolDefinition agentToolDefinition)
    {
        Verify.NotNull(agentToolDefinition.Configuration);

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
        Verify.NotNull(agentToolDefinition.Configuration);

        var specification = agentToolDefinition.GetRequiredConfiguration<Dictionary<object, object>>("specification");

        return new BinaryData(specification);
    }

    internal static OpenApiAuthDetails GetOpenApiAuthDetails(this AgentToolDefinition agentToolDefinition)
    {
        Verify.NotNull(agentToolDefinition.Configuration);

        var connectionId = agentToolDefinition.GetConfiguration<string>("connection_id");
        if (!string.IsNullOrEmpty(connectionId))
        {
            return new OpenApiConnectionAuthDetails(new OpenApiConnectionSecurityScheme(connectionId));
        }

        var audience = agentToolDefinition.GetConfiguration<string>("audience");
        if (!string.IsNullOrEmpty(audience))
        {
            return new OpenApiManagedAuthDetails(new OpenApiManagedSecurityScheme(audience));
        }

        return new OpenApiAnonymousAuthDetails();
    }

    private static AzureFunctionBinding GetAzureFunctionBinding(this AgentToolDefinition agentToolDefinition, string bindingType)
    {
        Verify.NotNull(agentToolDefinition.Configuration);

        var binding = agentToolDefinition.GetRequiredConfiguration<Dictionary<object, object>>(bindingType);
        if (!binding.TryGetValue("storage_service_endpoint", out var endpointValue) || endpointValue is not string storageServiceEndpoint)
        {
            throw new ArgumentException($"The configuration key '{bindingType}.storage_service_endpoint' is required.");
        }
        if (!binding.TryGetValue("queue_name", out var nameValue) || nameValue is not string queueName)
        {
            throw new ArgumentException($"The configuration key '{bindingType}.queue_name' is required.");
        }

        return new AzureFunctionBinding(new AzureFunctionStorageQueue(storageServiceEndpoint, queueName));
    }

    private static FileSearchRankingOptions? GetFileSearchRankingOptions(this AgentToolDefinition agentToolDefinition)
    {
        string? ranker = agentToolDefinition.GetConfiguration<string>("ranker");
        float? scoreThreshold = agentToolDefinition.GetConfiguration<float>("score_threshold");

        if (ranker is not null && scoreThreshold is not null)
        {
            return new FileSearchRankingOptions(ranker, (float)scoreThreshold!);
        }

        return null;
    }

    private static List<ToolConnection> GetToolConnections(this AgentToolDefinition agentToolDefinition)
    {
        Verify.NotNull(agentToolDefinition.Configuration);

        var toolConnections = agentToolDefinition.GetRequiredConfiguration<List<object>>("tool_connections");

        return toolConnections.Select(connectionId => new ToolConnection(connectionId.ToString())).ToList();
    }

    private static T GetRequiredConfiguration<T>(this AgentToolDefinition agentToolDefinition, string key)
    {
        Verify.NotNull(agentToolDefinition);
        Verify.NotNull(agentToolDefinition.Configuration);
        Verify.NotNull(key);

        if (agentToolDefinition.Configuration?.TryGetValue(key, out var value) ?? false)
        {
            if (value == null)
            {
                throw new ArgumentNullException($"The configuration key '{key}' must be a non null value.");
            }

            try
            {
                return (T)Convert.ChangeType(value, typeof(T));
            }
            catch (InvalidCastException)
            {
                throw new InvalidCastException($"The configuration key '{key}' value must be of type '{typeof(T)}' but is '{value.GetType()}'.");
            }
        }

        throw new ArgumentException($"The configuration key '{key}' is required.");
    }

    private static T? GetConfiguration<T>(this AgentToolDefinition agentToolDefinition, string key)
    {
        Verify.NotNull(agentToolDefinition);
        Verify.NotNull(key);

        if (agentToolDefinition.Configuration?.TryGetValue(key, out var value) ?? false)
        {
            if (value == null)
            {
                return default;
            }

            try
            {
                return (T?)Convert.ChangeType(value, typeof(T));
            }
            catch (InvalidCastException)
            {
                throw new InvalidCastException($"The configuration key '{key}' value must be of type '{typeof(T?)}' but is '{value.GetType()}'.");
            }
        }

        return default;
    }

    private static readonly BinaryData s_noParams = BinaryData.FromObjectAsJson(new { type = "object", properties = new { } });
}
