// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using Azure.Identity;
using ChatWithAgent.ApiService.Config;
using ChatWithAgent.Configuration;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Azure;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;

namespace ChatWithAgent.ApiService;

/// <summary>
/// Defines the Program class containing the application's entry point.
/// </summary>
public static class Program
{
    /// <summary>
    /// The main entry point for the application.
    /// </summary>
    /// <param name="args">The command-line arguments.</param>
    public static void Main(string[] args)
    {
        var builder = WebApplication.CreateBuilder(args);

        // Add service defaults & Aspire client integrations.
        builder.AddServiceDefaults();

        builder.Services.AddControllers();

        // Add services to the container.
        builder.Services.AddProblemDetails();

        // Load the service configuration.
        var config = new ServiceConfig(builder.Configuration);

        // Add Kernel
        builder.Services.AddKernel();

        // Add AI services.
        AddAIServices(builder, config.Host);

        // Add Vector Store.
        AddVectorStore(builder, config.Host.Rag);

        // Add Chat Completion Agent.
        AddAgent(builder, config.Agent);

        var app = builder.Build();

        // Configure the HTTP request pipeline.
        app.UseExceptionHandler();

        app.MapDefaultEndpoints();

        app.MapControllers();

        app.Run();
    }

    /// <summary>
    /// Adds AI services for chat completion and text embedding generation.
    /// </summary>
    /// <param name="builder">The web application builder.</param>
    /// <param name="config">Service configuration.</param>
    /// <exception cref="NotSupportedException"></exception>
    private static void AddAIServices(WebApplicationBuilder builder, HostConfig config)
    {
        // Add AzureOpenAI client.
        if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName || config.Rag?.AIEmbeddingService == AzureOpenAIEmbeddingsConfig.ConfigSectionName)
        {
            builder.AddAzureOpenAIClient(
                connectionName: HostConfig.AzureOpenAIConnectionStringName,
                configureSettings: (settings) => settings.Credential = builder.Environment.IsProduction()
                    ? new DefaultAzureCredential()
                    : new AzureCliCredential(),
                configureClientBuilder: clientBuilder =>
                {
                    clientBuilder.ConfigureOptions((options) =>
                    {
                        options.RetryPolicy = new ClientRetryPolicy(maxRetries: 3);
                    });
                });
        }

        // Add OpenAI client.
        if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName || config.Rag?.AIEmbeddingService == OpenAIEmbeddingsConfig.ConfigSectionName)
        {
            builder.AddOpenAIClient(HostConfig.OpenAIConnectionStringName);
        }

        // Add chat completion services.
        switch (config.AIChatService)
        {
            case AzureOpenAIChatConfig.ConfigSectionName:
            {
                builder.Services.AddAzureOpenAIChatCompletion(config.AzureOpenAIChat.DeploymentName, modelId: config.AzureOpenAIChat.ModelName);
                break;
            }
            case OpenAIChatConfig.ConfigSectionName:
            {
                builder.Services.AddOpenAIChatCompletion(config.OpenAIChat.ModelName);
                break;
            }
            default:
                throw new NotSupportedException($"AI chat service '{config.AIChatService}' is not supported.");
        }

        if (config.Rag is not null)
        {
            // Add text embedding generation services.
            switch (config.Rag.AIEmbeddingService)
            {
                case AzureOpenAIEmbeddingsConfig.ConfigSectionName:
                {
                    builder.Services.AddAzureOpenAITextEmbeddingGeneration(config.AzureOpenAIEmbeddings.DeploymentName, modelId: config.AzureOpenAIEmbeddings.ModelName);
                    break;
                }
                case OpenAIEmbeddingsConfig.ConfigSectionName:
                {
                    builder.Services.AddOpenAITextEmbeddingGeneration(config.OpenAIEmbeddings.ModelName);
                    break;
                }
                default:
                    throw new NotSupportedException($"AI embeddings service '{config.Rag.AIEmbeddingService}' is not supported.");
            }
        }
    }

    /// <summary>
    /// Adds the vector store to the service collection.
    /// </summary>
    /// <param name="builder">The web application builder.</param>
    /// <param name="config">The RAG configuration.</param>
    private static void AddVectorStore(WebApplicationBuilder builder, RagConfig? config)
    {
        if (config is not null)
        {
            // Add Vector Store
            switch (config.VectorStoreType)
            {
                case "InMemory":
                {
                    builder.Services.AddInMemoryVectorStoreRecordCollection<string, TextSnippet<string>>(config.CollectionName);
                    break;
                }
                default:
                    throw new NotSupportedException($"Vector store type '{config.VectorStoreType}' is not supported.");
            }

            // Register all the other required services.
            switch (config.VectorStoreType)
            {
                case "InMemory":
                    RegisterServices<string>(builder, config);
                    break;
                default:
                    throw new NotSupportedException($"Vector store type '{config.VectorStoreType}' is not supported.");
            }
        }

        static void RegisterServices<TKey>(WebApplicationBuilder builder, RagConfig ragConfig) where TKey : notnull
        {
            builder.Services.AddSingleton<UniqueKeyGenerator<string>>(new UniqueKeyGenerator<string>(() => Guid.NewGuid().ToString()));
            builder.Services.AddSingleton<IDataLoader, PdfLoader<TKey>>((sp) =>
            {
                UniqueKeyGenerator<TKey> uniqueKeyGenerator = sp.GetRequiredService<UniqueKeyGenerator<TKey>>();
                IVectorStoreRecordCollection<TKey, TextSnippet<TKey>> vectorStoreRecordCollection = sp.GetRequiredService<IVectorStoreRecordCollection<TKey, TextSnippet<TKey>>>();
                IChatCompletionService chatCompletionService = sp.GetRequiredService<IChatCompletionService>();
                ITextEmbeddingGenerationService textEmbeddingGenerationService = sp.GetRequiredService<ITextEmbeddingGenerationService>();
                ILoggerFactory loggerFactory = sp.GetRequiredService<ILoggerFactory>();

                return new PdfLoader<TKey>(
                    uniqueKeyGenerator,
                    vectorStoreRecordCollection,
                    textEmbeddingGenerationService,
                    chatCompletionService,
                    loggerFactory.CreateLogger<PdfLoader<TKey>>(),
                    ragConfig.PdfBatchSize,
                    ragConfig.PdfBatchLoadingDelayMilliseconds);
            });
        }
    }

    /// <summary>
    /// Adds the chat completion agent to the service collection.
    /// </summary>
    /// <param name="builder">The web application builder.</param>
    /// <param name="config">The agent configuration.</param>
    private static void AddAgent(WebApplicationBuilder builder, AgentConfig config)
    {
        // Add chat completion agent.
        builder.Services.AddTransient<ChatCompletionAgent>((sp) =>
        {
            return new ChatCompletionAgent()
            {
                Kernel = sp.GetRequiredService<Kernel>(),
                Name = config.Name,
                Description = config.Description,
                Instructions = config.Instructions
            };
        });
    }
}
