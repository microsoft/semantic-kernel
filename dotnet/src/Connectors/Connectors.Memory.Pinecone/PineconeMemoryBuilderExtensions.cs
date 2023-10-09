// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Plugins.Memory;

namespace Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

/// <summary>
/// Provides extension methods for the <see cref="MemoryBuilder"/> class to configure Pinecone connector.
/// </summary>
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
        builder.WithMemoryStore((loggerFactory, httpHandlerFactory) =>
        {
            var client = new PineconeClient(
                environment,
                apiKey,
                loggerFactory,
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory));

            return new PineconeMemoryStore(client, loggerFactory);
        });

        return builder;
    }
}
