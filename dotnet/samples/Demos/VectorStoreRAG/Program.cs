// Copyright (c) Microsoft. All rights reserved.

using Azure;
using Azure.Identity;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Data;
using VectorStoreRAG;
using VectorStoreRAG.Options;

HostApplicationBuilder builder = Host.CreateApplicationBuilder(args);

builder.Configuration
    .AddUserSecrets<Program>();

builder.Services.Configure<RagConfig>(builder.Configuration.GetSection(RagConfig.ConfigSectionName));

var vectorStoreRagConfig = new VectorStoreRagConfig(builder.Configuration);

var kernelBuilder = builder.Services.AddKernel()
    .AddAzureOpenAIChatCompletion(
        vectorStoreRagConfig.AzureOpenAIConfig.ChatDeploymentName,
        vectorStoreRagConfig.AzureOpenAIConfig.Endpoint,
        new AzureCliCredential())
    .AddAzureOpenAITextEmbeddingGeneration(
        vectorStoreRagConfig.AzureOpenAIEmbeddingsConfig.DeploymentName,
        vectorStoreRagConfig.AzureOpenAIEmbeddingsConfig.Endpoint,
        new AzureCliCredential());

switch (vectorStoreRagConfig.RagConfig.VectorStoreType)
{
    case "Qdrant":
        kernelBuilder.AddQdrantVectorStoreRecordCollection<Guid, TextSnippet<Guid>>(
            vectorStoreRagConfig.RagConfig.CollectionName,
            vectorStoreRagConfig.QdrantConfig.Host,
            vectorStoreRagConfig.QdrantConfig.Port,
            vectorStoreRagConfig.QdrantConfig.Https,
            vectorStoreRagConfig.QdrantConfig.ApiKey);
        break;
    case "AzureAISearch":
        kernelBuilder.AddAzureAISearchVectorStoreRecordCollection<TextSnippet<Guid>>(
            vectorStoreRagConfig.RagConfig.CollectionName,
            new Uri(vectorStoreRagConfig.AzureAISearchConfig.Endpoint),
            new AzureKeyCredential(vectorStoreRagConfig.AzureAISearchConfig.ApiKey));
        break;
    default:
        throw new NotSupportedException($"Vector store type '{vectorStoreRagConfig.RagConfig.VectorStoreType}' is not supported.");
}

switch (vectorStoreRagConfig.RagConfig.VectorStoreType)
{
    case "Qdrant":
        RegisterServices<Guid>(builder, kernelBuilder, vectorStoreRagConfig);
        break;
    case "AzureAISearch":
        RegisterServices<string>(builder, kernelBuilder, vectorStoreRagConfig);
        break;
    default:
        throw new NotSupportedException($"Vector store type '{vectorStoreRagConfig.RagConfig.VectorStoreType}' is not supported.");
}

using IHost host = builder.Build();

await host.RunAsync().ConfigureAwait(false);

static void RegisterServices<TKey>(HostApplicationBuilder builder, IKernelBuilder kernelBuilder, VectorStoreRagConfig vectorStoreRagConfig)
    where TKey : notnull
{
    kernelBuilder.AddVectorStoreTextSearch<TextSnippet<TKey>>(
        new TextSearchStringMapper((result) => (result as TextSnippet<TKey>)!.Text!),
        new TextSearchResultMapper((result) =>
        {
            var castResult = result as TextSnippet<TKey>;
            return new TextSearchResult(value: castResult!.Text) { Link = castResult.ReferenceLink };
        }));

    builder.Services.AddSingleton<UniqueKeyGenerator<Guid>>(new UniqueKeyGenerator<Guid>(() => Guid.NewGuid()));
    builder.Services.AddSingleton<IDataLoader, DataLoader<Guid>>();
    builder.Services.AddHostedService<RAGChatService<Guid>>();
}
