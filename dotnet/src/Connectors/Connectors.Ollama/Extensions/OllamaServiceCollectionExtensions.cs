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

            var chatClientBuilder = new ChatClientBuilder()
                .UseFunctionInvocation(config =>
                    config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());
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

            var chatClientBuilder = new ChatClientBuilder()
                .UseFunctionInvocation(config =>
                    config.MaximumIterationsPerRequest = MaxInflightAutoInvokes);

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());
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

            var builder = new EmbeddingGeneratorBuilder<string, Embedding<float>>();

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());
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

            var builder = new EmbeddingGeneratorBuilder<string, Embedding<float>>();

            var logger = serviceProvider.GetService<ILoggerFactory>()?.CreateLogger(ollamaClient.GetType());
            if (logger is not null)
            {
                builder.UseLogging(logger);
            }

            return builder.Use(ollamaClient).AsTextEmbeddingGenerationService(serviceProvider);
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
            => ollamaClient.AsTextEmbeddingGenerationService(serviceProvider));

        return services;
    }

    #endregion

    #region Private

    /// <summary>
    /// The maximum number of auto-invokes that can be in-flight at any given time as part of the current
    /// asynchronous chain of execution.
    /// </summary>
    /// <remarks>
    /// This is a fail-safe mechanism. If someone accidentally manages to set up execution settings in such a way that
    /// auto-invocation is invoked recursively, and in particular where a prompt function is able to auto-invoke itself,
    /// we could end up in an infinite loop. This const is a backstop against that happening. We should never come close
    /// to this limit, but if we do, auto-invoke will be disabled for the current flow in order to prevent runaway execution.
    /// With the current setup, the way this could possibly happen is if a prompt function is configured with built-in
    /// execution settings that opt-in to auto-invocation of everything in the kernel, in which case the invocation of that
    /// prompt function could advertize itself as a candidate for auto-invocation. We don't want to outright block that,
    /// if that's something a developer has asked to do (e.g. it might be invoked with different arguments than its parent
    /// was invoked with), but we do want to limit it. This limit is arbitrary and can be tweaked in the future and/or made
    /// configurable should need arise.
    /// </remarks>
    private const int MaxInflightAutoInvokes = 128;

    #endregion
}
