// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Ollama.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.Ollama.TextEmbedding;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Ollama connectors.
/// </summary>
public static class OllamaKernelBuilderExtensions
{
    /// <summary>
    /// Registers an Ollama text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="model">The name of the Ollama model.</param>
    /// <param name="endpoint">The endpoint URL for the text completion service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="setAsDefault">Indicates whether the service should be the default for its type.</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> to be used for making HTTP requests.
    /// If not provided, a default <see cref="HttpClient"/> instance will be used.</param>
    /// <returns>The modified <see cref="KernelBuilder"/> instance.</returns>
    public static KernelBuilder WithOllamaTextCompletionService(this KernelBuilder builder,
        string model,
        string? endpoint = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, (loggerFactory, httpHandlerFactory) =>
            new OllamaTextCompletion(
                model,
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory),
                endpoint),
                setAsDefault);

        return builder;
    }

    /// <summary>
    /// Registers an Ollama text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="model">The name of the Ollama model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="setAsDefault">Indicates whether the service should be the default for its type.</param>
    /// <returns>The <see cref="KernelBuilder"/> instance.</returns>
    public static KernelBuilder WithOllamaTextEmbeddingGenerationService(this KernelBuilder builder,
        string model,
        string endpoint,
        string? serviceId = null,
        bool setAsDefault = false)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (loggerFactory, httpHandlerFactory) =>
            new OllamaTextEmbeddingGeneration(
                model,
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient: null, loggerFactory),
                endpoint),
                setAsDefault);

        return builder;
    }

    /// <summary>
    /// Registers an Ollama text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="model">The name of the Ollama model.</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="serviceId">A local identifier for the given AI serviceю</param>
    /// <param name="setAsDefault">Indicates whether the service should be the default for its type.</param>
    /// <returns>The <see cref="KernelBuilder"/> instance.</returns>
    public static KernelBuilder WithOllamaTextEmbeddingGenerationService(this KernelBuilder builder,
        string model,
        HttpClient? httpClient = null,
        string? endpoint = null,
        string? serviceId = null,
        bool setAsDefault = false)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (loggerFactory, httpHandlerFactory) =>
            new OllamaTextEmbeddingGeneration(
                model,
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory),
                endpoint),
                setAsDefault);

        return builder;
    }
}
