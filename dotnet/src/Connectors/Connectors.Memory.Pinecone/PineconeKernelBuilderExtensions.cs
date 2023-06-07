// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
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
                GetHttpClient(parameters.Config, httpClient, parameters.Logger));

            return new PineconeMemoryStore(client, parameters.Logger);
        });

        return builder;
    }

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <param name="config">The kernel configuration.</param>
    /// <param name="httpClient">An optional pre-existing instance of HttpClient.</param>
    /// <param name="logger">An optional logger.</param>
    /// <returns>An instance of HttpClient.</returns>
    private static HttpClient GetHttpClient(KernelConfig config, HttpClient? httpClient, ILogger? logger)
    {
        if (httpClient == null)
        {
            var retryHandler = config.HttpHandlerFactory.Create(logger);
            retryHandler.InnerHandler = NonDisposableHttpClientHandler.Instance;
            return new HttpClient(retryHandler, false); // We should refrain from disposing the underlying SK default HttpClient handler as it would impact other HTTP clients that utilize the same handler.
        }

        return httpClient;
    }
}
