﻿// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Chroma;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Chroma memory connector.
/// </summary>
public static class ChromaMemoryBuilderExtensions
{
    /// <summary>
    /// Registers Chroma memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="endpoint">Chroma server endpoint URL.</param>
    /// <returns>Updated Memory builder including Chroma memory connector.</returns>
    public static MemoryBuilder WithChromaMemoryStore(this MemoryBuilder builder, string endpoint)
    {
        builder.WithMemoryStore((loggerFactory, injectedClient) =>
        {
            return new ChromaMemoryStore(
                HttpClientProvider.GetHttpClient(injectedClient),
                endpoint,
                loggerFactory);
        });

        return builder;
    }

    /// <summary>
    /// Registers Chroma memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="httpClient">The <see cref="HttpClient"/> instance used for making HTTP requests.</param>
    /// <param name="endpoint">Chroma server endpoint URL. If not specified, the base address of the HTTP client is used.</param>
    /// <returns>Updated Memory builder including Chroma memory connector.</returns>
    public static MemoryBuilder WithChromaMemoryStore(
        this MemoryBuilder builder,
        HttpClient httpClient,
        string? endpoint = null)
    {
        builder.WithMemoryStore((loggerFactory, injectedClient) =>
        {
            return new ChromaMemoryStore(
                HttpClientProvider.GetHttpClient(httpClient ?? injectedClient),
                endpoint,
                loggerFactory);
        });

        return builder;
    }
}
