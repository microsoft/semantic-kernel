// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;
using OllamaSharp;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for adding Ollama Text Generation service to the kernel builder.
/// </summary>
public static class OllamaServiceCollectionExtensions
{
    #region Text Generation

    /// <summary>
    /// Add Ollama Text Generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextGenerationService(
                modelId: modelId,
                endpoint: endpoint,
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Add Ollama Text Generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">Optional custom HttpClient, picked from ServiceCollection if not provided.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextGenerationService(
                modelId: modelId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Add Ollama Text Generation service to the kernel builder.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        string modelId,
        OllamaApiClient ollamaClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextGenerationService(
                modelId: modelId,
                ollamaClient: ollamaClient,
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Add Ollama Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaChatCompletion(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            var ollamaClient = new OllamaApiClient(endpoint, modelId);
            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());

            var chatClientBuilder = new ChatClientBuilder()
                .UseFunctionInvocation(config =>
                    config.MaximumIterationsPerRequest = 128);

            if (logger is not null)
            {
                chatClientBuilder.UseLogging(logger);
            }

            return chatClientBuilder.Use(ollamaClient).AsChatCompletionService(serviceProvider);
        });

        return services;
    }

    /// <summary>
    /// Add Ollama Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">Optional custom HttpClient, picked from ServiceCollection if not provided.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaChatCompletion(
        this IServiceCollection services,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            var ollamaClient = new OllamaApiClient(
                client: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                modelId);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());

            var chatClientBuilder = new ChatClientBuilder()
                .UseFunctionInvocation(config =>
                    config.MaximumIterationsPerRequest = 128);

            if (logger is not null)
            {
                chatClientBuilder.UseLogging(logger);
            }

            return chatClientBuilder.Use(ollamaClient).AsChatCompletionService(serviceProvider);
        });

        return services;
    }

    /// <summary>
    /// Add Ollama Chat Completion service to the kernel builder.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaChatCompletion(
        this IServiceCollection services,
        OllamaApiClient ollamaClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _)
            => ollamaClient.AsChatCompletionService(serviceProvider));

        return services;
    }

    #endregion

    #region Text Embeddings

    /// <summary>
    /// Add Ollama Text Embedding Generation services to the kernel builder.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var ollamaClient = new OllamaApiClient(endpoint, modelId);
            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());

            var builder = new EmbeddingGeneratorBuilder<string, Embedding<float>>();

            if (logger is not null)
            {
                builder.UseLogging(logger);
            }

            return builder.Use(ollamaClient).AsTextEmbeddingGenerationService(serviceProvider);
        });

        return services;
    }

    /// <summary>
    /// Add Ollama Text Embedding Generation services to the kernel builder.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">Optional custom HttpClient, picked from ServiceCollection if not provided.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var ollamaClient = new OllamaApiClient(
                client: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                defaultModel: modelId);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());

            var builder = new EmbeddingGeneratorBuilder<string, Embedding<float>>();

            if (logger is not null)
            {
                builder.UseLogging(logger);
            }

            return (ITextEmbeddingGenerationService)builder.Use(ollamaClient).AsEmbeddingGenerationService(serviceProvider);
        });

        return services;
    }

    /// <summary>
    /// Add Ollama Text Embeddings Generation service to the kernel builder.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextEmbeddingGeneration(
        this IServiceCollection services,
        OllamaApiClient ollamaClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _)
            => (ITextEmbeddingGenerationService)ollamaClient.AsEmbeddingGenerationService(serviceProvider));

        return services;
    }

    #endregion
}
