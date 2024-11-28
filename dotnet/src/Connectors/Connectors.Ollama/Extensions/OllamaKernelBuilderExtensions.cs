// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Connectors.Ollama;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;
using OllamaSharp;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods for adding Ollama Text Generation service to the kernel builder.
/// </summary>
public static class OllamaKernelBuilderExtensions
{
    #region Text Generation

    /// <summary>
    /// Add Ollama Text Generation service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaTextGeneration(
        this IKernelBuilder builder,
        string modelId,
        Uri endpoint,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextGenerationService(
                modelId: modelId,
                endpoint: endpoint,
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }

    /// <summary>
    /// Add Ollama Text Generation service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaTextGeneration(
        this IKernelBuilder builder,
        string modelId,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextGenerationService(
                modelId: modelId,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }

    /// <summary>
    /// Add Ollama Text Generation service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaTextGeneration(
        this IKernelBuilder builder,
        string modelId,
        OllamaApiClient ollamaClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new OllamaTextGenerationService(
                modelId: modelId,
                ollamaClient: ollamaClient,
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return builder;
    }

    #endregion

    #region Chat Completion

    /// <summary>
    /// Add Ollama Chat Completion service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOllamaChatCompletion(modelId, endpoint, serviceId);

        return builder;
    }

    /// <summary>
    /// Add Ollama Chat Completion service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaChatCompletion(
        this IKernelBuilder builder,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null
        )
    {
        Verify.NotNull(builder);

        builder.Services.AddOllamaChatCompletion(modelId, httpClient, serviceId);

        return builder;
    }

    /// <summary>
    /// Add Ollama Chat Completion service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaChatCompletion(
        this IKernelBuilder builder,
        OllamaApiClient ollamaClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOllamaChatCompletion(ollamaClient, serviceId);

        return builder;
    }

    #endregion

    #region Text Embeddings

    /// <summary>
    /// Add Ollama Text Embeddings Generation service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="endpoint">The endpoint to Ollama hosted service.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaTextEmbeddingGeneration(
        this IKernelBuilder builder,
        string modelId,
        Uri endpoint,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOllamaTextEmbeddingGeneration(modelId, endpoint, serviceId);

        return builder;
    }

    /// <summary>
    /// Add Ollama Text Embeddings Generation service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaTextEmbeddingGeneration(
        this IKernelBuilder builder,
        string modelId,
        HttpClient? httpClient = null,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOllamaTextEmbeddingGeneration(modelId, httpClient, serviceId);

        return builder;
    }

    /// <summary>
    /// Add Ollama Text Embeddings Generation service to the kernel builder.
    /// </summary>
    /// <param name="builder">The kernel builder.</param>
    /// <param name="ollamaClient">The Ollama Sharp library client.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated kernel builder.</returns>
    public static IKernelBuilder AddOllamaTextEmbeddingGeneration(
        this IKernelBuilder builder,
        OllamaApiClient ollamaClient,
        string? serviceId = null)
    {
        Verify.NotNull(builder);

        builder.Services.AddOllamaTextEmbeddingGeneration(ollamaClient, serviceId);

        return builder;
    }

    #endregion
}
