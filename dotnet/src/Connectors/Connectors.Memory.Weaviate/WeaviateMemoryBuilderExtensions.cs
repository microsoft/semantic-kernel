// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Weaviate connector.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
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
        builder.WithMemoryStore((loggerFactory, injectedClient) =>
        {
            return new WeaviateMemoryStore(
                HttpClientProvider.GetHttpClient(injectedClient),
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
        builder.WithMemoryStore((loggerFactory, injectedClient) =>
        {
            return new WeaviateMemoryStore(
                HttpClientProvider.GetHttpClient(httpClient ?? injectedClient),
                apiKey,
                endpoint,
                apiVersion,
                loggerFactory);
        });

        return builder;
    }
}
