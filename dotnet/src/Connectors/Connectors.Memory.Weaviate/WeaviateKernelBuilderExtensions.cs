// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Weaviate;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Weaviate memory connector.
/// </summary>
[Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
[EditorBrowsable(EditorBrowsableState.Never)]
public static class WeaviateKernelBuilderExtensions
{
    /// <summary>
    /// Registers Weaviate memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="endpoint">The Weaviate server endpoint URL.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <param name="apiVersion">The API version to use.</param>
    /// <returns>Self instance</returns>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static KernelBuilder WithWeaviateMemoryStore(
        this KernelBuilder builder,
        string endpoint,
        string? apiKey,
        string? apiVersion = null)
    {
        builder.WithMemoryStorage((loggerFactory, httpHandlerFactory) =>
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
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="httpClient">The optional <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">The Weaviate server endpoint URL. If not specified, the base address of the HTTP client is used.</param>
    /// <param name="apiKey">The API key for accessing Weaviate server.</param>
    /// <param name="apiVersion">The API version to use.</param>
    /// <returns>Self instance</returns>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static KernelBuilder WithWeaviateMemoryStore(this KernelBuilder builder,
        HttpClient httpClient,
        string? endpoint = null,
        string? apiKey = null,
        string? apiVersion = null)
    {
        builder.WithMemoryStorage((loggerFactory, httpHandlerFactory) =>
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
