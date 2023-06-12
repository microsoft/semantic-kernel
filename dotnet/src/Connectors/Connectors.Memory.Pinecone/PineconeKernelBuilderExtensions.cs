// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.SemanticKernel.Connectors.Memory.Pinecone;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="KernelBuilder"/> class to configure Pinecone connectors.
/// </summary>
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
    public static KernelBuilder WithPineconeMemoryStore(this KernelBuilder builder,
        string environment,
        string apiKey,
        HttpClient? httpClient = null)
    {
        builder.WithMemoryStorage((parameters) =>
        {
            var client = new PineconeClient(
                environment,
                apiKey,
                parameters.Logger,
                HttpClientProvider.GetHttpClient(parameters.Config, httpClient, parameters.Logger));

            return new PineconeMemoryStore(client, parameters.Logger);
        });

        return builder;
    }
}
