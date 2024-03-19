// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
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
    /// <param name="serviceId">A local identifier for the given memory store.</param>
    /// <returns>Updated Memory builder including Chroma memory connector.</returns>
    public static MemoryBuilder WithChromaMemoryStore(this MemoryBuilder builder, string endpoint, string? serviceId = null)
    {
        builder.Services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) =>
        {
            return new ChromaMemoryStore(
                HttpClientProvider.GetHttpClient(provider.GetService<HttpClient>()),
                endpoint,
                provider.GetService<ILoggerFactory>());
        });

        return builder;
    }
}
