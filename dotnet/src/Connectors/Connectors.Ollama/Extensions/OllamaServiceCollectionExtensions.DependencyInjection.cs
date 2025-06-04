// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Http;
using OllamaSharp;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extension methods for adding Ollama Text Generation service to the kernel builder.
/// </summary>
public static class OllamaServiceCollectionExtensions
{
    #region Text Embeddings

    /// <summary>
    /// Add Ollama Embedding Generator to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = ((IEmbeddingGenerator<string, Embedding<float>>)new OllamaApiClient(endpoint, modelId))
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build(serviceProvider);
        });
    }

    /// <summary>
    /// Add Ollama Embedding Generator to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">Optional custom HttpClient, picked from ServiceCollection if not provided.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
        {
            httpClient ??= HttpClientProvider.GetHttpClient(httpClient, serviceProvider);

            var loggerFactory = serviceProvider.GetService<ILoggerFactory>();

            var builder = ((IEmbeddingGenerator<string, Embedding<float>>)new OllamaApiClient(httpClient, modelId))
                .AsBuilder();

            if (loggerFactory is not null)
            {
                builder.UseLogging(loggerFactory);
            }

            return builder.Build(serviceProvider);
        });

        return services;
    }

    /// <summary>
    /// Add Ollama Embedding Generator to the service collection.
    /// </summary>
    /// <param name="services">The target service collection.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaEmbeddingGenerator(
        this IServiceCollection services,
        OllamaApiClient? ollamaClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
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

            return builder.Build(serviceProvider);
        });
    }

    #endregion
}
