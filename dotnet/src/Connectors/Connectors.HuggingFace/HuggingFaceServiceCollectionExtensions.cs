// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.HuggingFace;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.ImageToText;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="IServiceCollection"/> interface to configure Hugging Face connectors.
/// </summary>
public static class HuggingFaceServiceCollectionExtensions
{
    /// <summary>
    /// Adds an Hugging Face text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint URL for the text generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceTextGeneration(
        this IServiceCollection services,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceTextGenerationService(
                model,
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an Hugging Face text generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint URL for the text generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceTextGeneration(
        this IServiceCollection services,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceTextGenerationService(
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an Hugging Face chat completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint URL for the chat completion service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceChatCompletion(
        this IServiceCollection services,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceChatCompletionService(
                model,
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()
            ));
    }

    /// <summary>
    /// Adds an Hugging Face chat completion service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint URL for the chat completion service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceChatCompletion(
        this IServiceCollection services,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceChatCompletionService(
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()
            ));
    }

    /// <summary>
    /// Adds an Hugging Face text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Obsolete("Use AddHuggingFaceEmbeddingGenerator instead.")]
    public static IServiceCollection AddHuggingFaceTextEmbeddingGeneration(
        this IServiceCollection services,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceTextEmbeddingGenerationService(
                model,
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()
            ));
    }

    /// <summary>
    /// Adds an Hugging Face text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    [Obsolete("Use AddHuggingFaceEmbeddingGenerator instead.")]
    public static IServiceCollection AddHuggingFaceTextEmbeddingGeneration(
        this IServiceCollection services,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceTextEmbeddingGenerationService(
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()
            ));
    }

    /// <summary>
    /// Adds an Hugging Face image-to-text service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the image-to-text service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceImageToText(
        this IServiceCollection services,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IImageToTextService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceImageToTextService(
                model,
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds an Hugging Face image-to-text service with the specified configuration.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint for the image-to-text service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="services"/>.</returns>
    public static IServiceCollection AddHuggingFaceImageToText(
        this IServiceCollection services,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);

        return services.AddKeyedSingleton<IImageToTextService>(serviceId, (serviceProvider, _) =>
            new HuggingFaceImageToTextService(
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                serviceProvider.GetService<ILoggerFactory>()));
    }
}
