// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
using System;
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
using System;
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
using System;
>>>>>>> main
>>>>>>> Stashed changes
using System.Net.Http;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Connectors.Weaviate;
using Microsoft.SemanticKernel.Data;
using Microsoft.SemanticKernel.Http;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Extension methods to register Weaviate <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>
/// </summary>
public static class WeaviateServiceCollectionExtensions
{
    /// <summary>
    /// Register a Weaviate <see cref="IVectorStore"/> with the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddWeaviateVectorStore(
        this IServiceCollection services,
        HttpClient? httpClient = default,
        WeaviateVectorStoreOptions? options = default,
        string? serviceId = default)
    {
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var selectedHttpClient = HttpClientProvider.GetHttpClient(httpClient, sp);
                var selectedOptions = options ?? sp.GetService<WeaviateVectorStoreOptions>();
                return new WeaviateVectorStore(selectedHttpClient, options);
            });

        return services;
    }
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes

    /// <summary>
    /// Register a Weaviate <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> and <see cref="IVectorizedSearch{TRecord}"/> with the specified service ID.
    /// </summary>
    /// <typeparam name="TRecord">The type of the record.</typeparam>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> on.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="httpClient">
    /// <see cref="HttpClient"/> that is used to interact with Weaviate API.
    /// <see cref="HttpClient.BaseAddress"/> should point to remote or local cluster and API key can be configured via <see cref="HttpClient.DefaultRequestHeaders"/>.
    /// It's also possible to provide these parameters via <see cref="WeaviateVectorStoreOptions"/>.
    /// </param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <returns>Service collection.</returns>
    public static IServiceCollection AddWeaviateVectorStoreRecordCollection<TRecord>(
        this IServiceCollection services,
        string collectionName,
        HttpClient? httpClient = default,
        WeaviateVectorStoreRecordCollectionOptions<TRecord>? options = default,
        string? serviceId = default)
        where TRecord : class
    {
        services.AddKeyedTransient<IVectorStoreRecordCollection<Guid, TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                var selectedHttpClient = HttpClientProvider.GetHttpClient(httpClient, sp);
                var selectedOptions = options ?? sp.GetService<WeaviateVectorStoreRecordCollectionOptions<TRecord>>();

                return new WeaviateVectorStoreRecordCollection<TRecord>(selectedHttpClient, collectionName, selectedOptions);
            });

        AddVectorizedSearch<TRecord>(services, serviceId);

        return services;
    }

    /// <summary>
    /// Also register the <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> with the given <paramref name="serviceId"/> as a <see cref="IVectorizedSearch{TRecord}"/>.
    /// </summary>
    /// <typeparam name="TRecord">The type of the data model that the collection should contain.</typeparam>
    /// <param name="services">The service collection to register on.</param>
    /// <param name="serviceId">The service id that the registrations should use.</param>
    private static void AddVectorizedSearch<TRecord>(IServiceCollection services, string? serviceId)
        where TRecord : class
    {
        services.AddKeyedTransient<IVectorizedSearch<TRecord>>(
            serviceId,
            (sp, obj) =>
            {
                return sp.GetRequiredKeyedService<IVectorStoreRecordCollection<Guid, TRecord>>(serviceId);
            });
    }
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
}
