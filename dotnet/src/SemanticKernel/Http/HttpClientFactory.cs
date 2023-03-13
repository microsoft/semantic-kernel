// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Net.Http;

namespace Microsoft.SemanticKernel.Http;
internal sealed class HttpClientFactory : IHttpClientFactory, IDisposable
{
    /// <summary>
    /// HTTP clients cache.
    /// </summary>
    private readonly ConcurrentBag<HttpClient> _httpClients = new();

    /// <inheritdoc/>
    public HttpClient Create(HttpMessageHandler handler, bool disposeHandler)
    {
        var client = new HttpClient(handler, disposeHandler);

        this._httpClients.Add(client);

        return client;
    }

    /// <summary>
    /// Releases unmanaged resources.
    /// </summary>
    public void Dispose()
    {
        foreach (var httpClient in this._httpClients)
        {
            httpClient.Dispose();
        }
    }
}
