// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using Azure.Identity;
using ChatWithAgent.ApiService.Config;
using ChatWithAgent.ApiService.Resources;
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
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

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
        AddVectorStore(builder, config);

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
        if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName || config.Rag.AIEmbeddingService == AzureOpenAIEmbeddingsConfig.ConfigSectionName)
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
        if (config.AIChatService == AzureOpenAIChatConfig.ConfigSectionName || config.Rag.AIEmbeddingService == OpenAIEmbeddingsConfig.ConfigSectionName)
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

    /// <summary>
    /// Adds the vector store to the service collection.
    /// </summary>
    /// <param name="builder">The web application builder.</param>
    /// <param name="config">The RAG configuration.</param>
    private static void AddVectorStore(WebApplicationBuilder builder, ServiceConfig config)
    {
        // Add Vector Store
        switch (config.Host.Rag.VectorStoreType)
        {
            case "InMemory":
            {
                builder.Services.AddInMemoryVectorStoreRecordCollection<string, TextSnippet<string>>(config.Host.Rag.CollectionName);
                break;
            }
            default:
                throw new NotSupportedException($"Vector store type '{config.Host.Rag.VectorStoreType}' is not supported.");
        }

        // Register all the other required services.
        switch (config.Host.Rag.VectorStoreType)
        {
            case "InMemory":
                AddRagServicesa<string>(builder, config.Host.Rag);
                AddAgent<string>(builder);
                break;
            default:
                throw new NotSupportedException($"Vector store type '{config.Host.Rag.VectorStoreType}' is not supported.");
        }

        static void AddRagServicesa<TKey>(WebApplicationBuilder builder, RagConfig ragConfig) where TKey : notnull
        {
            // Add a text search implementation that uses the registered vector store record collection for search.
            builder.Services.AddVectorStoreTextSearch<TextSnippet<TKey>>(
                new TextSearchStringMapper((result) => (result as TextSnippet<TKey>)!.Text!),
                new TextSearchResultMapper((result) =>
                {
                    // Create a mapping from the Vector Store data type to the data type returned by the Text Search.
                    // This text search will ultimately be used in a plugin and this TextSearchResult will be returned to the prompt template
                    // when the plugin is invoked from the prompt template.
                    var castResult = result as TextSnippet<TKey>;
                    return new TextSearchResult(value: castResult!.Text!) { Name = castResult.ReferenceDescription };
                }));

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
    /// <typeparam name="TKey">The type of the data model key.</typeparam>
    private static void AddAgent<TKey>(WebApplicationBuilder builder)
    {
        PromptTemplateConfig templateConfig = new()
        {
            TemplateFormat = HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            Template = EmbeddedResource.Read("AgentDefinition.yaml")
        };

        HandlebarsPromptTemplateFactory handlebarsPromptTemplateFactory = new();

        // Add chat completion agent.
        builder.Services.AddTransient<ChatCompletionAgent>((sp) =>
        {
            Kernel kernel = sp.GetRequiredService<Kernel>();
            VectorStoreTextSearch<TextSnippet<TKey>> vectorStoreTextSearch = sp.GetRequiredService<VectorStoreTextSearch<TextSnippet<TKey>>>();

            // Add a search plugin to the kernel which we will use in the template below
            // to do a vector search for related information to the user query.
            kernel.Plugins.Add(vectorStoreTextSearch.CreateWithGetTextSearchResults("SearchPlugin"));

            return new ChatCompletionAgent(templateConfig, handlebarsPromptTemplateFactory)
            {
                Kernel = kernel,
            };
        });
    }
}
