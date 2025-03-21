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
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.Data;
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

        // Enable diagnostics.
        AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnostics", true);

        // Uncomment the following line to enable diagnostics with sensitive data: prompts, completions, function calls, and more.
        //AppContext.SetSwitch("Microsoft.SemanticKernel.Experimental.GenAI.EnableOTelDiagnosticsSensitive", true);

        // Enable SK traces using OpenTelemetry.Extensions.Hosting extensions.
        // An alternative approach to enabling traces can be found here: https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-aspire-dashboard?tabs=Powershell&pivots=programming-language-csharp 
        builder.Services.AddOpenTelemetry().WithTracing(b => b.AddSource("Microsoft.SemanticKernel*"));

        // Enable SK metrics using OpenTelemetry.Extensions.Hosting extensions.
        // An alternative approach to enabling metrics can be found here: https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-aspire-dashboard?tabs=Powershell&pivots=programming-language-csharp
        builder.Services.AddOpenTelemetry().WithMetrics(b => b.AddMeter("Microsoft.SemanticKernel*"));

        // Enable SK logs.
        // Log source and log level for SK is configured in appsettings.json.
        // An alternative approach to enabling logs can be found here: https://learn.microsoft.com/en-us/semantic-kernel/concepts/enterprise-readiness/observability/telemetry-with-aspire-dashboard?tabs=Powershell&pivots=programming-language-csharp

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
        AddVectorStore(builder, config.Host);

        // Add Agent.
        AddAgent(builder, config.Host);

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
    /// <param name="config">The host configuration.</param>
    private static void AddVectorStore(WebApplicationBuilder builder, HostConfig config)
    {
        // Don't add vector store if no collection name is provided. Allows for a basic experience where no data has been uploaded to the vector store yet.
        if (string.IsNullOrWhiteSpace(config.Rag.CollectionName))
        {
            return;
        }

        // Add Vector Store
        switch (config.Rag.VectorStoreType)
        {
            case AzureAISearchConfig.ConfigSectionName:
            {
                builder.AddAzureSearchClient(
                    connectionName: AzureAISearchConfig.ConnectionStringName,
                    configureSettings: (settings) => settings.Credential = builder.Environment.IsProduction()
                        ? new DefaultAzureCredential()
                        : new AzureCliCredential()
                );
                builder.Services.AddAzureAISearchVectorStoreRecordCollection<TextSnippet<string>>(config.Rag.CollectionName);
                builder.Services.AddVectorStoreTextSearch<TextSnippet<string>>();
                break;
            }
            default:
                throw new NotSupportedException($"Vector store type '{config.Rag.VectorStoreType}' is not supported.");
        }
    }

    /// <summary>
    /// Adds the chat completion agent to the service collection.
    /// </summary>
    /// <param name="builder">The web application builder.</param>
    /// <param name="config">The host configuration.</param>
    private static void AddAgent(WebApplicationBuilder builder, HostConfig config)
    {
        // Register agent without RAG if no collection name is provided. Allows for a basic experience where no data has been uploaded to the vector store yet.
        if (string.IsNullOrEmpty(config.Rag.CollectionName))
        {
            PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(EmbeddedResource.Read("AgentDefinition.yaml"));

            builder.Services.AddTransient<ChatCompletionAgent>((sp) =>
            {
                return new ChatCompletionAgent(templateConfig, new HandlebarsPromptTemplateFactory())
                {
                    Kernel = sp.GetRequiredService<Kernel>(),
                };
            });
        }
        else
        {
            // Register agent with RAG.
            PromptTemplateConfig templateConfig = KernelFunctionYaml.ToPromptTemplateConfig(EmbeddedResource.Read("AgentWithRagDefinition.yaml"));

            switch (config.Rag.VectorStoreType)
            {
                case AzureAISearchConfig.ConfigSectionName:
                {
                    AddAgentWithRag<string>(builder, templateConfig);
                    break;
                }
                default:
                    throw new NotSupportedException($"Vector store type '{config.Rag.VectorStoreType}' is not supported.");
            }
        }

        static void AddAgentWithRag<TKey>(WebApplicationBuilder builder, PromptTemplateConfig templateConfig)
        {
            builder.Services.AddTransient<ChatCompletionAgent>((sp) =>
            {
                Kernel kernel = sp.GetRequiredService<Kernel>();
                VectorStoreTextSearch<TextSnippet<TKey>> vectorStoreTextSearch = sp.GetRequiredService<VectorStoreTextSearch<TextSnippet<TKey>>>();

                // Add a search plugin to the kernel which we will use in the agent template
                // to do a vector search for related information to the user query.
                kernel.Plugins.Add(vectorStoreTextSearch.CreateWithGetTextSearchResults("SearchPlugin"));

                return new ChatCompletionAgent(templateConfig, new HandlebarsPromptTemplateFactory())
                {
                    Kernel = kernel,
                };
            });
        }
    }
}
