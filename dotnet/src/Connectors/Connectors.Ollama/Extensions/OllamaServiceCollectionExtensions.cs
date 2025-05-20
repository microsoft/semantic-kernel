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
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            return new OllamaTextGenerationService(
                modelId: modelId,
                endpoint: endpoint,
                loggerFactory: serviceProvider.GetService<ILoggerFactory>());
        });
    }

    /// <summary>
    /// Add Ollama Text Generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">Optional custom HttpClient, picked from ServiceCollection if not provided.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            return new OllamaTextGenerationService(
                modelId: modelId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>());
        });
    }

    /// <summary>
    /// Add Ollama Text Generation service to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        string modelId,
        OllamaApiClient ollamaClient,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            return new OllamaTextGenerationService(
                modelId: modelId,
                ollamaClient: ollamaClient,
                loggerFactory: loggerFactory);
        });
    }

    /// <summary>
    /// Add Ollama Text Generation service to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        OllamaApiClient? ollamaClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();
            ollamaClient ??= serviceProvider.GetKeyedService<OllamaApiClient>(serviceId);
            ollamaClient ??= serviceProvider.GetKeyedService<IOllamaApiClient>(serviceId) as OllamaApiClient;
            ollamaClient ??= serviceProvider.GetService<OllamaApiClient>();
            ollamaClient ??= serviceProvider.GetRequiredService<IOllamaApiClient>() as OllamaApiClient;

            if (ollamaClient is null)
            {
                throw new InvalidOperationException($"No {nameof(IOllamaApiClient)} implementations found in the service collection.");
            }

            return new OllamaTextGenerationService(
                ollamaClient: ollamaClient,
                loggerFactory: loggerFactory);
        });
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

        return services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var ollamaClient = (IChatClient)new OllamaApiClient(endpoint, modelId);

            var builder = ollamaClient.AsBuilder();
            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder
                .UseKernelFunctionInvocation(loggerFactory)
                .Build(serviceProvider)
                .AsChatCompletionService();
        });
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

        return services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            httpClient ??= HttpClientProvider.GetHttpClient(httpClient, serviceProvider);

            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var ollamaClient = (IChatClient)new OllamaApiClient(httpClient, modelId);

            var builder = ollamaClient.AsBuilder();
            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder
                .UseKernelFunctionInvocation(loggerFactory)
                .Build(serviceProvider)
                .AsChatCompletionService();
        });
    }

    /// <summary>
    /// Add Ollama Chat Completion service to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaChatCompletion(
        this IServiceCollection services,
        OllamaApiClient? ollamaClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();
            ollamaClient ??= serviceProvider.GetKeyedService<OllamaApiClient>(serviceId);
            ollamaClient ??= serviceProvider.GetKeyedService<IOllamaApiClient>(serviceId) as OllamaApiClient;
            ollamaClient ??= serviceProvider.GetService<OllamaApiClient>();
            ollamaClient ??= serviceProvider.GetRequiredService<IOllamaApiClient>() as OllamaApiClient;

            if (ollamaClient is null)
            {
                throw new InvalidOperationException($"No {nameof(IOllamaApiClient)} implementations found in the service collection.");
            }

            var builder = ((IChatClient)ollamaClient).AsBuilder();
            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder
                .UseKernelFunctionInvocation(loggerFactory)
                .Build(serviceProvider)
                .AsChatCompletionService();
        });
    }

    #endregion

    #region Text Embeddings

    /// <summary>
    /// Add Ollama Text Embedding Generation services to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    [Obsolete("Use AddOllamaEmbeddingGenerator instead.")]
    public static IServiceCollection AddOllamaTextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = ((IEmbeddingGenerator<string, Embedding<float>>)new OllamaApiClient(endpoint, modelId))
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build(serviceProvider).AsTextEmbeddingGenerationService(serviceProvider);
        });
    }

    /// <summary>
    /// Add Ollama Text Embedding Generation services to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">Optional custom HttpClient, picked from ServiceCollection if not provided.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    [Obsolete("Use AddOllamaEmbeddingGenerator instead.")]
    public static IServiceCollection AddOllamaTextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
        {
            httpClient ??= HttpClientProvider.GetHttpClient(httpClient, serviceProvider);

            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = ((IEmbeddingGenerator<string, Embedding<float>>)new OllamaApiClient(httpClient, modelId))
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build(serviceProvider).AsTextEmbeddingGenerationService(serviceProvider);
        });

        return services;
    }

    /// <summary>
    /// Add Ollama Text Embeddings Generation service to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    [Obsolete("Use AddOllamaEmbeddingGenerator instead.")]
    public static IServiceCollection AddOllamaTextEmbeddingGeneration(
        this IServiceCollection services,
        OllamaApiClient? ollamaClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();
            ollamaClient ??= serviceProvider.GetKeyedService<OllamaApiClient>(serviceId);
            ollamaClient ??= serviceProvider.GetKeyedService<IOllamaApiClient>(serviceId) as OllamaApiClient;
            ollamaClient ??= serviceProvider.GetService<OllamaApiClient>();
            ollamaClient ??= serviceProvider.GetRequiredService<IOllamaApiClient>() as OllamaApiClient;

            if (ollamaClient is null)
            {
                throw new InvalidOperationException($"No {nameof(IOllamaApiClient)} implementations found in the service collection.");
            }

            var builder = ((IEmbeddingGenerator<string, Embedding<float>>)ollamaClient)
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build(serviceProvider).AsTextEmbeddingGenerationService(serviceProvider);
        });
    }

    #endregion
}
