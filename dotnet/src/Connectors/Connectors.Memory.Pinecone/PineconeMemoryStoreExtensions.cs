// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.Pinecone;

/// <summary>
/// Extension methods for adding <see cref="PineconeMemoryStore"/>.
/// </summary>
public static class PineconeMemoryStoreExtensions
{
    /// <summary>
    /// Adds the <see cref="PineconeMemoryStore"/> implementation of <see cref="IMemoryStore"/> to the <see cref="IServiceCollection"/>.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the PineconeMemoryStore to.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddPineconeMemoryStore(this IServiceCollection services, string? serviceId = null)
        => services.AddKeyedSingleton<IMemoryStore, PineconeMemoryStore>(serviceId);

    /// <summary>
    /// Adds the <see cref="PineconeMemoryStore"/> implementation of <see cref="IMemoryStore"/> to the <see cref="IServiceCollection"/> and configures the <see cref="PineconeClient"/>.
    /// </summary>
    /// <param name="services">The IServiceCollection to add the PineconeMemoryStore to.</param>
    /// <param name="pineconeEnvironment">The Pinecone environment.</param>
    /// <param name="apiKey">The API key for accessing Pinecone.</param>
    /// <param name="serviceId">The optional service identifier.</param>
    /// <returns>The updated IServiceCollection.</returns>
    public static IServiceCollection AddPineconeMemoryStore(
        this IServiceCollection services,
        string pineconeEnvironment,
        string apiKey,
        string? serviceId = null)
    {
        services.AddKeyedSingleton<IPineconeClient>(serviceId, (_, _) => new PineconeClient(pineconeEnvironment, apiKey));
        return services.AddPineconeMemoryStore(serviceId);
    }
}
