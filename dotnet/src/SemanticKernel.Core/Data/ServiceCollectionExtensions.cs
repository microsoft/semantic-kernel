// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Data services on an <see cref="IServiceCollection"/>.
/// </summary>
[Experimental("SKEXP0001")]
public static class ServiceCollectionExtensions
{
    /// <summary>
    /// Register a Volatile <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>The service collection.</returns>
    [Obsolete("This has been replaced by the Microsoft.SemanticKernel.Connectors.InMemory nuget package.")]
    public static IServiceCollection AddVolatileVectorStore(this IServiceCollection services, string? serviceId = default)
    {
        services.AddKeyedSingleton<VolatileVectorStore, VolatileVectorStore>(serviceId);
        services.AddKeyedSingleton<IVectorStore>(serviceId, (sp, obj) => sp.GetRequiredKeyedService<VolatileVectorStore>(serviceId));
        return services;
    }

    /// <summary>
    /// Register a <see cref="VectorStoreTextSearch{TRecord}"/> instance with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="ITextSearch"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="stringMapper"><see cref="ITextSearchStringMapper" /> instance that can map a TRecord to a <see cref="string"/></param>
    /// <param name="resultMapper"><see cref="ITextSearchResultMapper" /> instance that can map a TRecord to a <see cref="TextSearchResult"/></param>
    /// <param name="options">Options used to construct an instance of <see cref="VectorStoreTextSearch{TRecord}"/></param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    [Obsolete("This has been replaced by the Microsoft.SemanticKernel.Connectors.InMemory nuget package.")]
    [UnconditionalSuppressMessage("Trimming", "IL2091:Target generic argument does not satisfy 'DynamicallyAccessedMembersAttribute' in target method or type. The generic parameter of the source method or type does not have matching annotations.", Justification = "This method is obsolete")]
    [UnconditionalSuppressMessage("Trimming", "IL2095:'DynamicallyAccessedMemberTypes' on the generic parameter of method or type don't match overridden generic parameter method or type. All overridden members must have the same 'DynamicallyAccessedMembersAttribute' usage.", Justification = "This method is obsolete")]

    public static IServiceCollection AddVolatileVectorStoreTextSearch<TKey, TRecord>(
        this IServiceCollection services,
        string collectionName,
        ITextSearchStringMapper? stringMapper = null,
        ITextSearchResultMapper? resultMapper = null,
        VectorStoreTextSearchOptions? options = null,
        string? serviceId = default)
        where TKey : notnull
    {
        // If we are not constructing the dependent services, add the VectorStoreTextSearch as transient, since we
        // cannot make assumptions about how dependent services are being managed.
        services.AddKeyedTransient<VectorStoreTextSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var vectorStore = sp.GetRequiredService<VolatileVectorStore>();
                var vectorSearch = vectorStore.GetCollection<TKey, TRecord>(collectionName);
                var generationService = sp.GetRequiredService<ITextEmbeddingGenerationService>();
                stringMapper ??= sp.GetRequiredService<ITextSearchStringMapper>();
                resultMapper ??= sp.GetRequiredService<ITextSearchResultMapper>();
                options ??= sp.GetService<VectorStoreTextSearchOptions>();
                return new VectorStoreTextSearch<TRecord>(vectorSearch, generationService, stringMapper, resultMapper, options);
            });

        return services;
    }
}
