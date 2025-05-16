// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for the <see cref="IKernelBuilder"/> class to configure Hugging Face connectors.
/// </summary>
public static class HuggingFaceKernelBuilderExtensions
{
    /// <summary>
    /// Adds an Hugging Face text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint URL for the text generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceTextGeneration(
        this IKernelBuilder builder,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceTextGeneration(model, endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an Hugging Face text generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint URL for the text generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceTextGeneration(
        this IKernelBuilder builder,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceTextGeneration(endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an Hugging Face chat completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint URL for the chat completion service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceChatCompletion(
        this IKernelBuilder builder,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceChatCompletion(model, endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an Hugging Face chat completion service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint URL for the chat completion service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceChatCompletion(
        this IKernelBuilder builder,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceChatCompletion(endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an Hugging Face text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Obsolete("Use AddHuggingFaceEmbeddingGenerator instead.")]
    public static IKernelBuilder AddHuggingFaceTextEmbeddingGeneration(
        this IKernelBuilder builder,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceTextEmbeddingGeneration(model, endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an Hugging Face text embedding generation service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint for the text embedding generation service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    [Obsolete("Use AddHuggingFaceEmbeddingGenerator instead.")]
    public static IKernelBuilder AddHuggingFaceTextEmbeddingGeneration(
        this IKernelBuilder builder,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceTextEmbeddingGeneration(endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds a HuggingFace embedding generator service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the embedding generator service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceEmbeddingGenerator(
        this IKernelBuilder builder,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceEmbeddingGenerator(model, endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds a HuggingFace embedding generator service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint for the embedding generator service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceEmbeddingGenerator(
        this IKernelBuilder builder,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceEmbeddingGenerator(endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an Hugging Face image-to-text service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="model">The name of the Hugging Face model.</param>
    /// <param name="endpoint">The endpoint for the image-to-text service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceImageToText(
        this IKernelBuilder builder,
        string model,
        Uri? endpoint = null,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceImageToText(model, endpoint, apiKey, serviceId, httpClient);

        return builder;
    }

    /// <summary>
    /// Adds an Hugging Face image-to-text service with the specified configuration.
    /// </summary>
    /// <param name="builder">The <see cref="IKernelBuilder"/> instance to augment.</param>
    /// <param name="endpoint">The endpoint for the image-to-text service.</param>
    /// <param name="apiKey">The API key required for accessing the Hugging Face service.</param>
    /// <param name="serviceId">A local identifier for the given AI service.</param>
    /// <param name="httpClient">The HttpClient to use with this service.</param>
    /// <returns>The same instance as <paramref name="builder"/>.</returns>
    public static IKernelBuilder AddHuggingFaceImageToText(
        this IKernelBuilder builder,
        Uri endpoint,
        string? apiKey = null,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddHuggingFaceImageToText(endpoint, apiKey, serviceId, httpClient);

        return builder;
    }
}
