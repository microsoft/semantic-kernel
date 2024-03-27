// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

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
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including Weaviate memory connector.</returns>
    public static MemoryBuilder WithWeaviateMemoryStore(
        this MemoryBuilder builder,
        string endpoint,
        string? apiKey,
        string? apiVersion = null,
        string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) =>
        {
            return new WeaviateMemoryStore(
                HttpClientProvider.GetHttpClient(provider.GetService<HttpClient>()),
                apiKey,
                endpoint,
                apiVersion,
                provider.GetService<ILoggerFactory>());
        });

        return builder;
    }
}
