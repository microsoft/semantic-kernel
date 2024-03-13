// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.TextGeneration;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding VertexAI generation services to the application.
/// </summary>
public static class VertexAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds Vertex AI Gemini Text Generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bearerKeyProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>
    /// This <paramref name="bearerKeyProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public static IServiceCollection AddVertexAIGeminiTextGeneration(
        this IServiceCollection services,
        string modelId,
        Func<string> bearerKeyProvider,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKeyProvider);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiTextGenerationService(
                modelId: modelId,
                bearerKeyProvider: bearerKeyProvider,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds Vertex AI Gemini Text Generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddVertexAIGeminiTextGeneration(
        this IServiceCollection services,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<ITextGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiTextGenerationService(
                modelId: modelId,
                bearerKey: bearerKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds Vertex AI Gemini Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bearerKeyProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>
    /// This <paramref name="bearerKeyProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public static IServiceCollection AddVertexAIGeminiChatCompletion(
        this IServiceCollection services,
        string modelId,
        Func<string> bearerKeyProvider,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKeyProvider);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiChatCompletionService(
                modelId: modelId,
                bearerKeyProvider: bearerKeyProvider,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }

    /// <summary>
    /// Adds Vertex AI Gemini Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddVertexAIGeminiChatCompletion(
        this IServiceCollection services,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiChatCompletionService(
                modelId: modelId,
                bearerKey: bearerKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }

    /// <summary>
    /// Adds Vertex AI embeddings generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Embeddings Generation service to.</param>
    /// <param name="modelId">The model for embeddings generation.</param>
    /// <param name="bearerKeyProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>
    /// This <paramref name="bearerKeyProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public static IServiceCollection AddVertexAIEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        Func<string> bearerKeyProvider,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKeyProvider);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAITextEmbeddingGenerationService(
                modelId: modelId,
                bearerKeyProvider: bearerKeyProvider,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Adds Vertex AI embeddings generation service to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Embeddings Generation service to.</param>
    /// <param name="modelId">The model for embeddings generation.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddVertexAIEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAITextEmbeddingGenerationService(
                modelId: modelId,
                bearerKey: bearerKey,
                location: location,
                projectId: projectId,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }
}
