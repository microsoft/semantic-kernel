// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Azure.Core;
using Microsoft.SemanticKernel.Connectors.Memory.AzureCognitiveSearch;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Azure Cognitive Search connectors.
/// </summary>
public static class AzureSearchServiceKernelBuilderExtensions
{
    /// <summary>
    /// Registers Azure Cognitive Search Memory Store.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="apiKey">The Api key used to authenticate requests against the Search service.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureCognitiveSearchMemory(this KernelBuilder builder,
        string endpoint,
        string apiKey,
        HttpClient? httpClient = null)
    {
        builder.WithMemory((parameters) =>
        {
            return new AzureCognitiveSearchMemory(
                endpoint,
                apiKey,
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger));
        });

        return builder;
    }

    /// <summary>
    /// Registers Azure Cognitive Search Memory Store.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="endpoint">Azure Cognitive Search URI, e.g. "https://contoso.search.windows.net"</param>
    /// <param name="credentials">The token credential used to authenticate requests against the Search service.</param>
    /// <param name="httpClient">Custom <see cref="HttpClient"/> for HTTP requests.</param>
    /// <returns>Self instance</returns>
    public static KernelBuilder WithAzureCognitiveSearchMemory(this KernelBuilder builder,
        string endpoint,
        TokenCredential credentials,
        HttpClient? httpClient = null)
    {
        builder.WithMemory((parameters) =>
        {
            return new AzureCognitiveSearchMemory(
                endpoint,
                credentials,
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger));
        });

        return builder;
    }
}
