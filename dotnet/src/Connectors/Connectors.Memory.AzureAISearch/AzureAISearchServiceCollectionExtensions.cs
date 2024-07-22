// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.Core;
using Azure.Search.Documents.Indexes;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Extension methods to register Azure AI Search <see cref="IVectorStore"/> instances on an <see cref="IServiceCollection"/>.
/// </summary>
public static class AzureAISearchServiceCollectionExtensions
{
    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the specified service ID and where <see cref="SearchIndexClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optoinal options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(this IServiceCollection services, string? serviceId = default, AzureAISearchVectorStoreOptions? options = default)
    {
        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var searchIndexClient = sp.GetRequiredService<SearchIndexClient>();
                var selectedOptions = options ?? sp.GetService<AzureAISearchVectorStoreOptions>();

                return new AzureAISearchVectorStore(
                    searchIndexClient,
                    selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the provided <see cref="Uri"/> and <see cref="TokenCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optoinal options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(this IServiceCollection services, Uri endpoint, TokenCredential tokenCredential, string? serviceId = default, AzureAISearchVectorStoreOptions? options = default)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(tokenCredential);

        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var searchIndexClient = new SearchIndexClient(endpoint, tokenCredential);
                var selectedOptions = options ?? sp.GetService<AzureAISearchVectorStoreOptions>();

                return new AzureAISearchVectorStore(
                    searchIndexClient,
                    selectedOptions);
            });

        return services;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="services">The <see cref="IServiceCollection"/> to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optoinal options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IServiceCollection AddAzureAISearchVectorStore(this IServiceCollection services, Uri endpoint, AzureKeyCredential credential, string? serviceId = default, AzureAISearchVectorStoreOptions? options = default)
    {
        Verify.NotNull(endpoint);
        Verify.NotNull(credential);

        services.AddKeyedTransient<IVectorStore>(
            serviceId,
            (sp, obj) =>
            {
                var searchIndexClient = new SearchIndexClient(endpoint, credential);
                var selectedOptions = options ?? sp.GetService<AzureAISearchVectorStoreOptions>();

                return new AzureAISearchVectorStore(
                    searchIndexClient,
                    selectedOptions);
            });

        return services;
    }
}
