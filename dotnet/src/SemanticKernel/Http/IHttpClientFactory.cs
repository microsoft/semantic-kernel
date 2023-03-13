// Copyright (c) Microsoft. All rights reserved.

using System.Net.Http;

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// The Http client factory.
/// </summary>
internal interface IHttpClientFactory
{
    /// <summary>
    /// Creates an instance of the HttpClient class.
    /// </summary>
    /// <param name="handler">Handler responsible for processing the HTTP response messages.</param>
    /// <param name="disposeHandler">Flag indicating if the inner handler should be disposed of by HttpClient.Dispose or not.</param>
    /// <returns>An instance of HttpClient class.</returns>
    HttpClient Create(HttpMessageHandler handler, bool disposeHandler);
}
