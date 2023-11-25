// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;
using Microsoft.Extensions.Logging;

/// <summary>
/// Provides functionality for retrieving instances of HttpClient.
/// </summary>
internal static class HttpClientProvider
{
    private static readonly HttpClientHandler s_sharedHandler = new();

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <param name="httpClient">An optional pre-existing instance of HttpClient.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(HttpClient? httpClient, ILoggerFactory? loggerFactory) =>
        httpClient ??
        new HttpClient(s_sharedHandler, disposeHandler: false);
}
