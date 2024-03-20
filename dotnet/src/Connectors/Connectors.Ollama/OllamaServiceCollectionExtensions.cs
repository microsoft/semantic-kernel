// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel.Connectors.Ollama;

/// <summary>
/// Extension methods for adding Ollama Text Generation service to the kernel builder.
/// </summary>
public static class OllamaServiceCollectionExtensions
{
    /// <summary>
    /// Add Ollama Text Generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Ollama Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="baseUri">The base uri to Ollama hosted service.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextGeneration(
        this IServiceCollection services,
        string modelId,
        Uri baseUri,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextGenerationService(
                model: modelId,
                baseUri: baseUri,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Add Ollama Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Ollama Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="baseUri">The base uri to Ollama hosted service.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddOllamaChatCompletion(
        this IServiceCollection services,
        string modelId,
        Uri baseUri,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new OllamaChatCompletionService(
                model: modelId,
                baseUri: baseUri,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));

        return services;
    }

    /// <summary>
    /// Add Ollama Text Embedding Generation services to the kernel builder.
    /// </summary>
    /// <param name="services">The service collection to add the Ollama Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="baseUri">The base uri to Ollama hosted service.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IServiceCollection AddOllamaTextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        Uri baseUri,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextEmbeddingGenerationService(
                model: modelId,
                baseUri: baseUri,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }
}
