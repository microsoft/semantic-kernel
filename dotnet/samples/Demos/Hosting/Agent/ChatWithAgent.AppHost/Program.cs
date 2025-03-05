// Copyright (c) Microsoft. All rights reserved.

using ChatWithAgent.AppHost.Extensions;
using ChatWithAgent.Configuration;

var builder = DistributedApplication.CreateBuilder(args);

// Load host configuration.
var hostConfig = new HostConfig(builder.Configuration);

// Add Api Service AI upstream dependencies
var aiServices = AddAIServices(builder, hostConfig);

// Add Api Service
var apiService = builder.AddProject<Projects.ChatWithAgent_ApiService>("apiservice")
    .WithEnvironment(hostConfig)  // Add some host configuration as environment variables so that the Api Service can access them
    .WithReferences(aiServices);

// Add Web Frontend
builder.AddProject<Projects.ChatWithAgent_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();

static List<IResourceBuilder<IResourceWithConnectionString>> AddAIServices(IDistributedApplicationBuilder builder, HostConfig config)
{
    if (config.AIChatService != AzureOpenAIChatConfig.ConfigSectionName &&
        config.AIChatService != OpenAIChatConfig.ConfigSectionName)
    {
        throw new NotSupportedException($"AI service '{config.AIChatService}' is not supported.");
    }

    if (config.AIEmbeddingsService != AzureOpenAIEmbeddingsConfig.ConfigSectionName &&
        config.AIEmbeddingsService != OpenAIEmbeddingsConfig.ConfigSectionName)
    {
        throw new NotSupportedException($"AI service '{config.AIEmbeddingsService}' is not supported.");
    }

    List<IResourceBuilder<IResourceWithConnectionString>> aiResources = [];

    // Add Azure OpenAI service and configured AI models
    if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName || config.AIEmbeddingsService == AzureOpenAIEmbeddingsConfig.ConfigSectionName)
    {
        if (builder.ExecutionContext.IsPublishMode)
        {
            aiResources.Add(builder.AddAzureOpenAIResources(config));
        }
        else
        {
            // Use an existing Azure OpenAI service via connection string
            aiResources.Add(builder.AddConnectionString(HostConfig.AzureOpenAIConnectionStringName));
        }
    }

    // Add OpenAI service via connection string
    if (config.AIChatService == OpenAIChatConfig.ConfigSectionName || config.AIEmbeddingsService == OpenAIEmbeddingsConfig.ConfigSectionName)
    {
        aiResources.Add(builder.AddConnectionString(HostConfig.OpenAIConnectionStringName));
    }

    return aiResources;
}
