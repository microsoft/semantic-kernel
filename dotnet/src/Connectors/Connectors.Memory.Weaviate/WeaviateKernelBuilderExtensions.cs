// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Weaviate memory connector.
/// </summary>
public static class WeaviateKernelBuilderExtensions
{
    /// <summary>
    /// Registers Weaviate memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="endpoint">The Weaviate server endpoint URL.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithWeaviateMemoryStore(this KernelBuilder builder, string endpoint, string? apiKey)
    {
        builder.WithMemoryStorage((loggerFactory) =>
        {
            return new WeaviateMemoryStore(
                HttpClientProvider.GetHttpClient(builder.HttpHandlerFactory, null, loggerFactory),
                apiKey,
                endpoint,
                loggerFactory);
        });

        return builder;
    }

    /// <summary>
    /// Registers Weaviate memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">The Weaviate server endpoint URL. If not specified, the base address of the HTTP client is used.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithWeaviateMemoryStore(this KernelBuilder builder,
        HttpClient httpClient,
        string? endpoint = null,
        string? apiKey = null)
    {
        builder.WithMemoryStorage((loggerFactory) =>
        {
            return new WeaviateMemoryStore(
                HttpClientProvider.GetHttpClient(builder.HttpHandlerFactory, httpClient, loggerFactory),
                apiKey,
                endpoint,
                loggerFactory);
        });

        return builder;
    }
}
