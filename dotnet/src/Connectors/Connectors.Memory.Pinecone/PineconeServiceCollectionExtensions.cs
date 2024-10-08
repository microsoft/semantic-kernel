// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Pinecone;
using Microsoft.SemanticKernel.Data;
using Sdk = Pinecone;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Pinecone <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class PineconeServiceCollectionExtensions
{
    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStore(this IServiceCollection services, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        // If we are not constructing the PineconeClient, add the IVectorStore as transient, since we
        // cannot make assumptions about how PineconeClient is being managed.
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var pineconeClient = sp.GetRequiredService<Sdk.PineconeClient>();
                var selectedOptions = options ?? sp.GetService<PineconeVectorStoreOptions>();

                return new PineconeVectorStore(
                    pineconeClient,
                    selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register a Pinecone <see cref="IVectorStore"/> with the specified service ID and where <see cref="Sdk.PineconeClient"/> is constructed using the provided apikey.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="apiKey">The api key for Pinecone.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    public static IServiceCollection AddPineconeVectorStore(this IServiceCollection services, string apiKey, PineconeVectorStoreOptions? options = default, string? serviceId = default)
    {
        services.AddKeyedSingleton<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var pineconeClient = new Sdk.PineconeClient(apiKey);
                var selectedOptions = options ?? sp.GetService<PineconeVectorStoreOptions>();

                return new PineconeVectorStore(
                    pineconeClient,
                    selectedOptions);
            });

        return services;
    }
}
