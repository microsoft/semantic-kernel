// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides functionality for retrieving instances of HttpClient.
/// </summary>
internal static class HttpClientProvider
{
    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <param name="httpHandlerFactory">The <see cref="IDelegatingHandlerFactory"/> to be used when the HttpClient is not provided already</param>
    /// <param name="httpClient">An optional pre-existing instance of HttpClient.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(IDelegatingHandlerFactory httpHandlerFactory, HttpClient? httpClient, ILoggerFactory? loggerFactory)
    {
        if (httpClient is null)
        {
            var providedHttpHandler = httpHandlerFactory.Create(loggerFactory);
            providedHttpHandler.InnerHandler = NonDisposableHttpClientHandler.Instance;
            return new HttpClient(providedHttpHandler, false); // We should refrain from disposing the underlying SK default HttpClient handler as it would impact other HTTP clients that utilize the same handler.
        }

        return httpClient;
    }
}
