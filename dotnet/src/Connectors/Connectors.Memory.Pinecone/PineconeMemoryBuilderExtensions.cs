// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net.Http;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

#pragma warning disable SKEXP0001 // IMemoryStore is experimental (but we're obsoleting)

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Pinecone connector.
/// </summary>
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and PineconeVectorStore")]
public static class PineconeMemoryBuilderExtensions
{
    /// <summary>
    /// Registers Pinecone memory connector.
    /// </summary>
    /// <param name="builder">The <see cref="MemoryBuilder"/> instance.</param>
    /// <param name="environment">The environment for Pinecone.</param>
    /// <param name="apiKey">The API key for accessing Pinecone services.</param>
    /// <param name="httpClient">An optional HttpClient instance for making HTTP requests.</param>
    /// <returns>Updated Memory builder including Pinecone memory connector.</returns>
    public static MemoryBuilder WithPineconeMemoryStore(
        this MemoryBuilder builder,
        string environment,
        string apiKey,
        HttpClient? httpClient = null)
    {
        builder.WithMemoryStore((loggerFactory, injectedClient) =>
        {
            var client = new PineconeClient(
                environment,
                apiKey,
                loggerFactory,
                HttpClientProvider.GetHttpClient(httpClient ?? injectedClient));

            return new PineconeMemoryStore(client, loggerFactory);
        });

        return builder;
    }
}
