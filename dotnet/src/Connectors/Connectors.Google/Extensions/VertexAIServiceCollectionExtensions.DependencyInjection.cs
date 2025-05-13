// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.Extensions.DependencyInjection;

/// <summary>
/// Extensions for adding VertexAI generation services to the application.
/// </summary>
public static class VertexAIServiceCollectionExtensions
{
    /// <summary>
    /// Add Vertex AI <see cref="IEmbeddingGenerator{String, Embedding}"/> to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Embeddings Generation service to.</param>
    /// <param name="modelId">The model for embeddings generation.</param>
    /// <param name="bearerTokenProvider">The Bearer Key provider for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="apiVersion">The version of the Vertex API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated service collection.</returns>
    /// <remarks>
    /// This <paramref name="bearerTokenProvider"/> will be called on every request,
    /// when providing the token consider using caching strategy and refresh token logic
    /// when it is expired or close to expiration.
    /// </remarks>
    public static IServiceCollection AddVertexAIEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        Func<ValueTask<string>> bearerTokenProvider,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerTokenProvider);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new VertexAIEmbeddingGenerator(
                modelId: modelId,
                bearerTokenProvider: bearerTokenProvider,
                location: location,
                projectId: projectId,
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }

    /// <summary>
    /// Add Vertex AI <see cref="IEmbeddingGenerator{String, Embedding}"/> to the specified service collection.
    /// </summary>
    /// <param name="services">The service collection to add the Gemini Embeddings Generation service to.</param>
    /// <param name="modelId">The model for embeddings generation.</param>
    /// <param name="bearerKey">The Bearer Key for authentication.</param>
    /// <param name="location">The location to process the request</param>
    /// <param name="projectId">Your project ID</param>
    /// <param name="apiVersion">The version of the Vertex API.</param>
    /// <param name="serviceId">Optional service ID.</param>
    /// <param name="httpClient">The optional custom HttpClient.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddVertexAIEmbeddingGenerator(
        this IServiceCollection services,
        string modelId,
        string bearerKey,
        string location,
        string projectId,
        VertexAIVersion apiVersion = VertexAIVersion.V1,
        string? serviceId = null,
        HttpClient? httpClient = null)
    {
        Verify.NotNull(services);
        Verify.NotNull(modelId);
        Verify.NotNull(bearerKey);
        Verify.NotNull(location);
        Verify.NotNull(projectId);

        return services.AddKeyedSingleton<IEmbeddingGenerator<string, Embedding<float>>>(serviceId, (serviceProvider, _) =>
            new VertexAIEmbeddingGenerator(
                modelId: modelId,
                bearerKey: bearerKey,
                location: location,
                projectId: projectId,
                apiVersion: apiVersion,
                httpClient: HttpClientProvider.GetHttpClient(httpClient, serviceProvider),
                loggerFactory: serviceProvider.GetService<ILoggerFactory>()));
    }
}
