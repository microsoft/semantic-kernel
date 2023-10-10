// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Chroma;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Chroma memory connector.
/// </summary>
[Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. Use ChromaMemoryBuilderExtensions instead.")]
[EditorBrowsable(EditorBrowsableState.Never)]
public static class ChromaKernelBuilderExtensions
{
    /// <summary>
    /// Registers Chroma memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="endpoint">Chroma server endpoint URL.</param>
    /// <returns>Self instance.</returns>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. Use ChromaMemoryBuilderExtensions.WithChromaMemoryStore instead.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static KernelBuilder WithChromaMemoryStore(this KernelBuilder builder, string endpoint)
    {
        builder.WithMemoryStorage((loggerFactory, httpHandlerFactory) =>
        {
            return new ChromaMemoryStore(
                HttpClientProvider.GetHttpClient(httpHandlerFactory, null, loggerFactory),
                endpoint,
                loggerFactory);
        });

        return builder;
    }

    /// <summary>
    /// Registers Chroma memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance.</param>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">Chroma server endpoint URL. If not specified, the base address of the HTTP client is used.</param>
    /// <returns>Self instance.</returns>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. Use ChromaMemoryBuilderExtensions.WithChromaMemoryStore instead.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static KernelBuilder WithChromaMemoryStore(this KernelBuilder builder,
        HttpClient httpClient,
        string? endpoint = null)
    {
        builder.WithMemoryStorage((loggerFactory, httpHandlerFactory) =>
        {
            return new ChromaMemoryStore(
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory),
                endpoint,
                loggerFactory);
        });

        return builder;
    }
}
