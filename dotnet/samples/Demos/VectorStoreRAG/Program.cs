// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using Azure;
using Azure.AI.OpenAI;
using Azure.Identity;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;
using OpenAI;
using VectorStoreRAG;
using VectorStoreRAG.Options;

HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

// Configure configuration and load the application configuration.
builder.Configuration.AddUserSecrets<Program>();
builder.Services.Configure<RagConfig>(builder.Configuration.GetSection(RagConfig.ConfigSectionName));
var appConfig = new ApplicationConfig(builder.Configuration);

// Create a cancellation token and source to pass to the application service to allow them
// to request a graceful application shutdown.
CancellationTokenSource appShutdownCancellationTokenSource = new();
CancellationToken appShutdownCancellationToken = appShutdownCancellationTokenSource.Token;
builder.Services.AddKeyedSingleton("AppShutdown", appShutdownCancellationTokenSource);

// Register the kernel with the dependency injection container
// and add Chat Completion and Text Embedding Generation services.
var kernelBuilder = builder.Services.AddKernel();

switch (appConfig.RagConfig.AIChatService)
{
    case "AzureOpenAI":
        kernelBuilder.AddAzureOpenAIChatCompletion(
            appConfig.AzureOpenAIConfig.ChatDeploymentName,
            appConfig.AzureOpenAIConfig.Endpoint,
            new AzureCliCredential());
        break;
    case "OpenAI":
        kernelBuilder.AddOpenAIChatCompletion(
            appConfig.OpenAIConfig.ModelId,
            appConfig.OpenAIConfig.ApiKey,
            appConfig.OpenAIConfig.OrgId);
        break;
    default:
        throw new NotSupportedException($"AI Chat Service type '{appConfig.RagConfig.AIChatService}' is not supported.");
}

switch (appConfig.RagConfig.AIEmbeddingService)
{
    case "AzureOpenAIEmbeddings":
        builder.Services.AddSingleton<IEmbeddingGenerator>(
            sp => new AzureOpenAIClient(new Uri(appConfig.AzureOpenAIEmbeddingsConfig.Endpoint), new AzureCliCredential())
                .GetEmbeddingClient(appConfig.AzureOpenAIEmbeddingsConfig.DeploymentName)
                .AsIEmbeddingGenerator());
        break;
    case "OpenAIEmbeddings":
        builder.Services.AddSingleton<IEmbeddingGenerator>(
            sp => new OpenAIClient(appConfig.OpenAIEmbeddingsConfig.ApiKey)
                .GetEmbeddingClient(appConfig.OpenAIEmbeddingsConfig.ModelId)
                .AsIEmbeddingGenerator());
        break;
    default:
        throw new NotSupportedException($"AI Embedding Service type '{appConfig.RagConfig.AIEmbeddingService}' is not supported.");
}

// Add the configured vector store record collection type to the
// dependency injection container.
switch (appConfig.RagConfig.VectorStoreType)
{
    case "AzureAISearch":
        kernelBuilder.Services.AddAzureAISearchCollection<TextSnippet<string>>(
            appConfig.RagConfig.CollectionName,
            new Uri(appConfig.AzureAISearchConfig.Endpoint),
            new AzureKeyCredential(appConfig.AzureAISearchConfig.ApiKey));
        break;
    case "CosmosMongoDB":
        kernelBuilder.Services.AddCosmosMongoCollection<TextSnippet<string>>(
            appConfig.RagConfig.CollectionName,
            appConfig.CosmosMongoConfig.ConnectionString,
            appConfig.CosmosMongoConfig.DatabaseName);
        break;
    case "CosmosNoSql":
        kernelBuilder.Services.AddCosmosNoSqlCollection<TextSnippet<string>>(
            appConfig.RagConfig.CollectionName,
            appConfig.CosmosNoSqlConfig.ConnectionString,
            appConfig.CosmosNoSqlConfig.DatabaseName);
        break;
    case "InMemory":
        kernelBuilder.Services.AddInMemoryVectorStoreRecordCollection<string, TextSnippet<string>>(
            appConfig.RagConfig.CollectionName);
        break;
    case "Qdrant":
        kernelBuilder.Services.AddQdrantCollection<Guid, TextSnippet<Guid>>(
            appConfig.RagConfig.CollectionName,
            appConfig.QdrantConfig.Host,
            appConfig.QdrantConfig.Port,
            appConfig.QdrantConfig.Https,
            appConfig.QdrantConfig.ApiKey);
        break;
    case "Redis":
        kernelBuilder.Services.AddRedisJsonCollection<TextSnippet<string>>(
            appConfig.RagConfig.CollectionName,
            appConfig.RedisConfig.ConnectionConfiguration);
        break;
    case "Weaviate":
        kernelBuilder.Services.AddWeaviateCollection<TextSnippet<Guid>>(
            // Weaviate collection names must start with an upper case letter.
            char.ToUpper(appConfig.RagConfig.CollectionName[0], CultureInfo.InvariantCulture) + appConfig.RagConfig.CollectionName.Substring(1),
            endpoint: new Uri(appConfig.WeaviateConfig.Endpoint),
            apiKey: null);
        break;
    default:
        throw new NotSupportedException($"Vector store type '{appConfig.RagConfig.VectorStoreType}' is not supported.");
}

// Register all the other required services.
switch (appConfig.RagConfig.VectorStoreType)
{
    case "AzureAISearch":
    case "CosmosMongoDB":
    case "CosmosNoSql":
    case "InMemory":
    case "Redis":
        RegisterServices<string>(builder, kernelBuilder, appConfig);
        break;
    case "Qdrant":
    case "Weaviate":
        RegisterServices<Guid>(builder, kernelBuilder, appConfig);
        break;
    default:
        throw new NotSupportedException($"Vector store type '{appConfig.RagConfig.VectorStoreType}' is not supported.");
}

// Build and run the host.
using IHost host = builder.Build();
await host.RunAsync(appShutdownCancellationToken).ConfigureAwait(false);

static void RegisterServices<TKey>(HostApplicationBuilder builder, IKernelBuilder kernelBuilder, ApplicationConfig vectorStoreRagConfig)
    where TKey : notnull
{
    // Add a text search implementation that uses the registered vector store record collection for search.
    kernelBuilder.AddVectorStoreTextSearch<TextSnippet<TKey>>();

    // Add the key generator and data loader to the dependency injection container.
    builder.Services.AddSingleton<UniqueKeyGenerator<Guid>>(new UniqueKeyGenerator<Guid>(() => Guid.NewGuid()));
    builder.Services.AddSingleton<UniqueKeyGenerator<string>>(new UniqueKeyGenerator<string>(() => Guid.NewGuid().ToString()));
    builder.Services.AddSingleton<IDataLoader, DataLoader<TKey>>();

    // Add the main service for this application.
    builder.Services.AddHostedService<RAGChatService<TKey>>();
}
