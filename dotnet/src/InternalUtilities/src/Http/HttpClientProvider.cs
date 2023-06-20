// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel;

/// <summary>
/// Provides functionality for retrieving instances of HttpClient.
/// </summary>
internal static class HttpClientProvider
{
    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <param name="config">The kernel configuration.</param>
    /// <param name="httpClient">An optional pre-existing instance of HttpClient.</param>
    /// <param name="logger">An optional logger.</param>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(KernelConfig config, HttpClient? httpClient, ILogger? logger)
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
