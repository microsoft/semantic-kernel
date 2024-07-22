// Copyright (c) Microsoft. All rights reserved.

using System;
using Azure;
using Azure.Core;
using Azure.Search.Documents.Indexes;
using Microsoft.SemanticKernel.Data;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;

/// <summary>
/// Extension methods to register Azure AI Search <see cref="IVectorStore"/> instances on the <see cref="IKernelBuilder"/>.
/// </summary>
public static class AzureAISearchKernelBuilderExtensions
{
    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the specified service ID and where <see cref="SearchIndexClient"/> is retrieved from the dependency injection container.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStore(this IKernelBuilder builder, string? serviceId = default, AzureAISearchVectorStoreOptions? options = default)
    {
        builder.Services.AddAzureAISearchVectorStore(serviceId, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the provided <see cref="Uri"/> and <see cref="TokenCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="tokenCredential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStore(this IKernelBuilder builder, Uri endpoint, TokenCredential tokenCredential, string? serviceId = default, AzureAISearchVectorStoreOptions? options = default)
    {
        builder.Services.AddAzureAISearchVectorStore(endpoint, tokenCredential, serviceId, options);
        return builder;
    }

    /// <summary>
    /// Register an Azure AI Search <see cref="IVectorStore"/> with the provided <see cref="Uri"/> and <see cref="AzureKeyCredential"/> and the specified service ID.
    /// </summary>
    /// <param name="builder">The builder to register the <see cref="IVectorStore"/> on.</param>
    /// <param name="endpoint">The service endpoint for Azure AI Search.</param>
    /// <param name="credential">The credential to authenticate to Azure AI Search with.</param>
    /// <param name="serviceId">An optional service id to use as the service key.</param>
    /// <param name="options">Optional options to further configure the <see cref="IVectorStore"/>.</param>
    /// <returns>The kernel builder.</returns>
    public static IKernelBuilder AddAzureAISearchVectorStore(this IKernelBuilder builder, Uri endpoint, AzureKeyCredential credential, string? serviceId = default, AzureAISearchVectorStoreOptions? options = default)
    {
        builder.Services.AddAzureAISearchVectorStore(endpoint, credential, serviceId, options);
        return builder;
    }
}
