// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

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
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including Pinecone memory connector.</returns>
    public static MemoryBuilder WithPineconeMemoryStore(
        this MemoryBuilder builder,
        string environment,
        string apiKey,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton(serviceId, (provider, _) =>
        {
            var client = new PineconeClient(
                environment,
                apiKey,
                provider.GetService<ILoggerFactory>(),
                HttpClientProvider.GetHttpClient(provider.GetService<HttpClient>()));

            return client;
        });

        builder.Services.AddKeyedSingleton<IMemoryStore, PineconeMemoryStore>(serviceId);

        return builder;
    }
}
