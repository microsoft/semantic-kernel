// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Pinecone connectors.
/// </summary>
[Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. Use PineconeMemoryBuilderExtensions instead.")]
[EditorBrowsable(EditorBrowsableState.Never)]
public static class PineconeKernelBuilderExtensions
{
    /// <summary>
    /// Registers Pinecone Memory Store.
    /// </summary>
    /// <param name="builder">The <see cref="KernelBuilder"/> instance</param>
    /// <param name="environment">The environment for Pinecone.</param>
    /// <param name="apiKey">The API key for accessing Pinecone services.</param>
    /// <param name="httpClient">An optional HttpClient instance for making HTTP requests.</param>
    /// <returns>Self instance</returns>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. Use PineconeMemoryBuilderExtensions.WithPineconeMemoryStore instead.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public static KernelBuilder WithPineconeMemoryStore(this KernelBuilder builder,
        string environment,
        string apiKey,
        HttpClient? httpClient = null)
    {
        builder.WithMemoryStorage((loggerFactory, httpHandlerFactory) =>
        {
            var client = new PineconeClient(
                environment,
                apiKey,
                loggerFactory,
                HttpClientProvider.GetHttpClient(httpHandlerFactory, httpClient, loggerFactory));

            return new PineconeMemoryStore(client, loggerFactory);
        });

        return builder;
    }
}
