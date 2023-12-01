// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextCompletion;
using Microsoft.SemanticKernel.Connectors.AI.HuggingFace.TextEmbedding;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Hugging Face connectors.
/// </summary>
public static class HuggingFaceKernelBuilderExtensions
{
    /// <summary>
    /// Adds an Hugging Face text completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="endpoint">The endpoint URL for the text completion service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithHuggingFaceTextCompletion(
        this KernelBuilder builder,
        string model,
        string? apiKey = null,
        string? endpoint = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(model);

        return builder.ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
                new HuggingFaceTextCompletion(model, apiKey, HttpClientProvider.GetHttpClient(httpClient, serviceProvider), endpoint));
        });
    }

    /// <summary>
    /// Adds an Hugging Face text completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="endpoint">The endpoint URL for the text completion service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceTextCompletion(
        this IServiceCollection services,
        string model,
        string? apiKey = null,
        string? endpoint = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(model);

        return services.AddKeyedSingleton<ITextCompletion>(serviceId, (serviceProvider, _) =>
            new HuggingFaceTextCompletion(model, apiKey, HttpClientProvider.GetHttpClient(serviceProvider), endpoint));
    }

    /// <summary>
    /// Adds an Hugging Face text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static KernelBuilder WithHuggingFaceTextEmbeddingGeneration(
        this KernelBuilder builder,
        string model,
        string? endpoint = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);
        Verify.NotNull(model);

        return builder.ConfigureServices(c =>
        {
            c.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
                new HuggingFaceTextEmbeddingGeneration(model, HttpClientProvider.GetHttpClient(httpClient, serviceProvider), endpoint));
        });
    }

    /// <summary>
    /// Adds an Hugging Face text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceTextEmbeddingGeneration(
        this IServiceCollection services,
        string model,
        string? endpoint = null,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(model);

        return services.AddKeyedSingleton<ITextEmbeddingGeneration>(serviceId, (serviceProvider, _) =>
            new HuggingFaceTextEmbeddingGeneration(model, HttpClientProvider.GetHttpClient(serviceProvider), endpoint));
    }
}
