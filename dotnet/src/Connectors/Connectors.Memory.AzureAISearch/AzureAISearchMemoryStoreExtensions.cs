// Copyright (c) Microsoft. All rights reserved.

using Azure.Core;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Connectors.AzureAISearch;
/// <summary>
/// Extension methods for adding Azure AI Search memory store to the service collection.
/// </summary>
public static class AzureAISearchMemoryStoreExtensions
{
    /// <summary>
    /// Adds an Azure AI Search memory store to the service collection using the provided endpoint and API key.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="endpoint">The Azure AI Search endpoint.</param>
    /// <param name="apiKey">The API key for accessing Azure AI Search.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAzureAISearchMemoryStore(this IServiceCollection services, string endpoint, string apiKey, string? serviceId = null) =>
        services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) => new AzureAISearchMemoryStore(endpoint, apiKey));

    /// <summary>
    /// Adds an Azure AI Search memory store to the service collection using the provided endpoint and token credential.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="endpoint">The Azure AI Search endpoint.</param>
    /// <param name="credential">The token credential for accessing Azure AI Search.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAzureAISearchMemoryStore(this IServiceCollection services, string endpoint, TokenCredential credential, string? serviceId = null) =>
        services.AddKeyedSingleton<IMemoryStore>(serviceId, (provider, _) => new AzureAISearchMemoryStore(endpoint, credential));

    /// <summary>
    /// Adds an Azure AI Search memory store to the service collection using the default service ID.
    /// </summary>
    /// <param name="services">The service collection.</param>
    /// <param name="serviceId">The optional service ID.</param>
    /// <returns>The updated service collection.</returns>
    public static IServiceCollection AddAzureAISearchMemoryStore(this IServiceCollection services, string? serviceId = null) =>
        services.AddKeyedSingleton<IMemoryStore, AzureAISearchMemoryStore>(serviceId);
}
