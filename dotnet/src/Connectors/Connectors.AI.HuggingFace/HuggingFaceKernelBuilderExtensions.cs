// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of KernelConfig
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

public static class HuggingFaceKernelBuilderExtensions
{
    /// <summary>
    /// Registers an Hugging Face text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint URL for the text completion service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Indicates whether the service should be the default for its type.</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> to be used for making HTTP requests.
    /// If not provided, a default <see cref="HttpClient"/> instance will be used.</param>
    /// <returns>The modified <see cref="KernelBuilder"/> instance.</returns>
    public static KernelBuilder WithHuggingFaceTextCompletionService(this KernelBuilder builder,
        string model,
        string? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextCompletion>(serviceId, (parameters) =>
            new HuggingFaceTextCompletion(
                model,
                endpoint,
                apiKey,
                GetHttpClient(parameters.Config, httpClient, parameters.Logger)),
                setAsDefault);

        return builder;
    }

    /// <summary>
    /// Registers an Hugging Face text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="serviceId">A local identifier for the given AI service</param>
    /// <param name="setAsDefault">Indicates whether the service should be the default for its type.</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <returns>The <see cref="KernelBuilder"/> instance.</returns>
    public static KernelBuilder WithHuggingFaceTextEmbeddingGenerationService(this KernelBuilder builder,
        string model,
        string? endpoint = null,
        string? serviceId = null,
        bool setAsDefault = false,
        HttpClient? httpClient = null)
    {
        builder.WithAIService<ITextEmbeddingGeneration>(serviceId, (parameters) =>
            new HuggingFaceTextEmbeddingGeneration(
                model,
                endpoint,
                GetHttpClient(parameters.Config, httpClient, parameters.Logger)),
                setAsDefault);
        return builder;
    }

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <param name="config">The kernel configuration.</param>
    /// <param name="httpClient">An optional pre-existing instance of HttpClient.</param>
    /// <param name="logger">An optional logger.</param>
    /// <returns>An instance of HttpClient.</returns>
    private static HttpClient GetHttpClient(KernelConfig config, HttpClient? httpClient, ILogger? logger)
    {
        if (httpClient == null)
        {
            var retryHandler = config.HttpHandlerFactory.Create(logger);
            retryHandler.InnerHandler = NonDisposableHttpClientHandler.Instance;
            return new HttpClient(retryHandler, false); // We should refrain from disposing the underlying SK default HttpClient handler as it would impact other HTTP clients that utilize the same handler.
        }

        return httpClient;
    }
}
