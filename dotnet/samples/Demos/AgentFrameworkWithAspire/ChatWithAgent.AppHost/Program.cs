// Copyright (c) Microsoft. All rights reserved.

using ChatWithAgent.AppHost.Extensions;
using ChatWithAgent.Configuration;

var builder = DistributedApplication.CreateBuilder(args);

// Load host configuration.
var hostConfig = new HostConfig(builder.Configuration);

// Add Api Service AI upstream dependencies
var aiServices = AddAIServices(builder, hostConfig);

// Add Vector Store
var vectorStore = AddVectorStore(builder, hostConfig);

// Add Api Service
var apiService = builder.AddProject<Projects.ChatWithAgent_ApiService>("apiservice")
    .WithEnvironment(hostConfig)  // Add some host configuration as environment variables so that the Api Service can access them
    .WithReferences(aiServices)
    .WithReference(vectorStore);

// Add Web Frontend
builder.AddProject<Projects.ChatWithAgent_Web>("webfrontend")
    .WithExternalHttpEndpoints()
    .WithReference(apiService)
    .WaitFor(apiService);

builder.Build().Run();

static List<IResourceBuilder<IResourceWithConnectionString>> AddAIServices(IDistributedApplicationBuilder builder, HostConfig config)
{
    IResourceBuilder<IResourceWithConnectionString>? chatResource = null;
    IResourceBuilder<IResourceWithConnectionString>? embeddingsResource = null;

    // Add Azure OpenAI service and configured AI models
    if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName || config.Rag.AIEmbeddingService == AzureOpenAIEmbeddingsConfig.ConfigSectionName)
    {
        if (builder.ExecutionContext.IsPublishMode)
        {
            // Add Azure OpenAI service
            var azureOpenAI = builder.AddAzureOpenAI(HostConfig.AzureOpenAIConnectionStringName);

            // Add chat deployment
            if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName)
            {
                chatResource = azureOpenAI.AddDeployment(new AzureOpenAIDeployment(
                    name: config.AzureOpenAIChat.DeploymentName,
                    modelName: config.AzureOpenAIChat.ModelName,
                    modelVersion: config.AzureOpenAIChat.ModelVersion,
                    skuName: config.AzureOpenAIChat.SkuName,
                    skuCapacity: config.AzureOpenAIChat.SkuCapacity)
                );
            }

            // Add deployment
            if (config.Rag.AIEmbeddingService == AzureOpenAIEmbeddingsConfig.ConfigSectionName)
            {
                embeddingsResource = azureOpenAI.AddDeployment(new AzureOpenAIDeployment(
                    name: config.AzureOpenAIEmbeddings.DeploymentName,
                    modelName: config.AzureOpenAIEmbeddings.ModelName,
                    modelVersion: config.AzureOpenAIEmbeddings.ModelVersion,
                    skuName: config.AzureOpenAIEmbeddings.SkuName,
                    skuCapacity: config.AzureOpenAIEmbeddings.SkuCapacity)
                );
            }
        }
        else
        {
            // Use an existing Azure OpenAI service via connection string
            chatResource = embeddingsResource = builder.AddConnectionString(HostConfig.AzureOpenAIConnectionStringName);
        }
    }

    // Add OpenAI service via connection string
    if (config.AIChatService == OpenAIChatConfig.ConfigSectionName || config.Rag.AIEmbeddingService == OpenAIEmbeddingsConfig.ConfigSectionName)
    {
        chatResource = embeddingsResource = builder.AddConnectionString(HostConfig.OpenAIConnectionStringName);
    }

    if (chatResource is null)
    {
        throw new NotSupportedException($"AI Chat service '{config.AIChatService}' is not supported.");
    }

    if (embeddingsResource is null)
    {
        throw new NotSupportedException($"AI Embedding service '{config.Rag.AIEmbeddingService}' is not supported.");
    }

    return [chatResource, embeddingsResource];
}

static IResourceBuilder<IResourceWithConnectionString> AddVectorStore(IDistributedApplicationBuilder builder, HostConfig config)
{
    switch (config.Rag.VectorStoreType)
    {
        case AzureAISearchConfig.ConfigSectionName:
        {
            return builder.ExecutionContext.IsPublishMode ?
                builder.AddAzureSearch(AzureAISearchConfig.ConnectionStringName) :
                builder.AddConnectionString(AzureAISearchConfig.ConnectionStringName);
        }
        default:
        {
            throw new NotSupportedException($"Vector Store type '{config.Rag.VectorStoreType}' is not supported.");
        }
    }
}
