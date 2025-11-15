// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.VoyageAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Reranking;

#pragma warning disable IDE0039 // Use local function

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for <see cref="IServiceCollection"/> to configure VoyageAI connectors.
/// </summary>
[Experimental("SKEXP0001")]
public static class VoyageAIServiceCollectionExtensions
{
    #region Text Embedding

    /// <summary>
    /// Adds the VoyageAI text embedding generation service to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The VoyageAI model ID (e.g., "voyage-3-large", "voyage-code-3").</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint. Defaults to https://api.voyageai.com/v1.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddVoyageAITextEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? endpoint = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, VoyageAITextEmbeddingGenerationService> factory =
            (serviceProvider, _) =>
                new(modelId,
                    apiKey,
                    endpoint,
                    HttpClientProvider.GetHttpClient(serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, factory);

        return services;
    }

    #endregion

    #region Contextualized Embedding

    /// <summary>
    /// Adds the VoyageAI contextualized embedding generation service to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The VoyageAI model ID (e.g., "voyage-3-large").</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint. Defaults to https://api.voyageai.com/v1.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddVoyageAIContextualizedEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? endpoint = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, VoyageAIContextualizedEmbeddingGenerationService> factory =
            (serviceProvider, _) =>
                new(modelId,
                    apiKey,
                    endpoint,
                    HttpClientProvider.GetHttpClient(serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, factory);

        return services;
    }

    #endregion

    #region Multimodal Embedding

    /// <summary>
    /// Adds the VoyageAI multimodal embedding generation service to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The VoyageAI model ID (e.g., "voyage-multimodal-3").</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint. Defaults to https://api.voyageai.com/v1.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddVoyageAIMultimodalEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? endpoint = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, VoyageAIMultimodalEmbeddingGenerationService> factory =
            (serviceProvider, _) =>
                new(modelId,
                    apiKey,
                    endpoint,
                    HttpClientProvider.GetHttpClient(serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, factory);

        return services;
    }

    #endregion

    #region Reranking

    /// <summary>
    /// Adds the VoyageAI text reranking service to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="modelId">The VoyageAI model ID (e.g., "rerank-2.5", "rerank-2.5-lite").</param>
    /// <param name="apiKey">The VoyageAI API key.</param>
    /// <param name="endpoint">Optional API endpoint. Defaults to https://api.voyageai.com/v1.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddVoyageAITextReranking(
        this IServiceCollection services,
        string modelId,
        string apiKey,
        string? endpoint = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNullOrWhiteSpace(modelId);
        Verify.NotNullOrWhiteSpace(apiKey);

        Func<IServiceProvider, object?, VoyageAITextRerankingService> factory =
            (serviceProvider, _) =>
                new(modelId,
                    apiKey,
                    endpoint,
                    HttpClientProvider.GetHttpClient(serviceProvider),
                    serviceProvider.GetService<ILoggerFactory>());

        services.AddKeyedSingleton<ITextRerankingService>(serviceId, factory);

        return services;
    }

    #endregion
}
