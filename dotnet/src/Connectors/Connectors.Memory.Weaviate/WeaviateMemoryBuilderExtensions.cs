// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Plugins.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Weaviate connector.
/// </summary>
public static class WeaviateMemoryBuilderExtensions
{
    /// <summary>
    /// Registers Weaviate memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="endpoint">The Weaviate server endpoint URL.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <param name="apiVersion">The API version to use.</param>
    /// <returns>Updated Memory builder including Weaviate memory connector.</returns>
    public static MemoryBuilder WithWeaviateMemoryStore(
        this MemoryBuilder builder,
        string endpoint,
        string? apiKey,
        string? apiVersion = null)
    {
        builder.WithMemoryStore((loggerFactory, httpHandlerFactory) =>
        {
            return new WeaviateMemoryStore(
                HttpClientProvider.GetHttpClient(httpHandlerFactory, null, loggerFactory),
                apiKey,
                endpoint,
                apiVersion,
                loggerFactory);
        });

        return builder;
    }

    /// <summary>
    /// Registers Weaviate memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">The Weaviate server endpoint URL. If not specified, the base address of the HTTP client is used.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <param name="apiVersion">The API version to use.</param>
    /// <returns>Updated Memory builder including Weaviate memory connector.</returns>
    public static MemoryBuilder WithWeaviateMemoryStore(
        this MemoryBuilder builder,
        HttpClient httpClient,
        string? endpoint = null,
        string? apiKey = null,
        string? apiVersion = null)
    {
        builder.WithMemoryStore((loggerFactory, httpHandlerFactory) =>
        {
            return new WeaviateMemoryStore(
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory),
                apiKey,
                endpoint,
                apiVersion,
                loggerFactory);
        });

        return builder;
    }
}
