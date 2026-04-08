// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Embeddings;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extensions for adding VertexAI generation services to the application.
/// </summary>
public static class VertexAIServiceCollectionExtensions
{
    /// <summary>
    /// Adds Vertex AI Gemini Chat Completion and Text Generation services to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Text Generation service to.</param>
    /// <param name="modelId">The model for text generation.</param>
    /// <param name="bearerTokenProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="apiVersion">The version of the Vertex API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>
    /// This <paramref name="bearerTokenProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public static IServiceCollection AddVertexAIGeminiChatCompletion(
        this IServiceCollection services,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        string? serviceId = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerTokenProvider);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        services.AddKeyedSingleton<IChatCompletionService>(serviceId, (serviceProvider, _) =>
            new VertexAIGeminiChatCompletionService(
                modelId: modelId,
                bearerTokenProvider: bearerTokenProvider,
                location: location,
                projectId: projectId,
                apiVersion: apiVersion,
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
    /// <param name="apiVersion">The version of the Vertex API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddVertexAIGeminiChatCompletion(
        this IServiceCollection services,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
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
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
        return services;
    }

    /// <summary>
    /// Adds Vertex AI <see cref="ITextEmbeddingGenerationService"/> to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Embeddings Generation service to.</param>
    /// <param name="modelId">The model for embeddings generation.</param>
    /// <param name="bearerTokenProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="apiVersion">The version of the Vertex API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>
    /// This <paramref name="bearerTokenProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    [Obsolete("Use AddVertexAIEmbeddingGenerator instead.")]
    public static IServiceCollection AddVertexAIEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        string? serviceId = null,
        int? dimensions = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerTokenProvider);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<ITextEmbeddingGenerationService>(serviceId, (serviceProvider, _) =>
            new VertexAITextEmbeddingGenerationService(
                modelId: modelId,
                bearerTokenProvider: bearerTokenProvider,
                location: location,
                projectId: projectId,
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>(),
                dimensions: dimensions));
    }

    /// <summary>
    /// Adds Vertex AI <see cref="ITextEmbeddingGenerationService"/> to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Embeddings Generation service to.</param>
    /// <param name="modelId">The model for embeddings generation.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="apiVersion">The version of the Vertex API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="dimensions">The number of dimensions that the model should use. If not specified, the default number of dimensions will be used.</param>
    /// <returns>The updated service collection.</returns>
    [Obsolete("Use AddVertexAIEmbeddingGenerator instead.")]
    public static IServiceCollection AddVertexAIEmbeddingGeneration(
        this IServiceCollection services,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        string? serviceId = null,
        int? dimensions = null)
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
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>(),
                dimensions: dimensions));
    }
}
