// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
#if NET
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Cryptography.X509Certificates;
#endif
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Http;

#pragma warning disable CA2000 // Ownership is transferred to HttpClient or NetworkStream.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Creates the built-in OpenAPI HTTP client and binds validated DNS addresses to its connections.
/// </summary>
internal static class OpenApiHttpClientProvider
{
#if NET
    internal static readonly HttpRequestOptionsKey<IPAddress[]> ValidatedAddressesKey = new("OpenApiValidatedAddresses");
#endif

    /// <summary>
    /// Creates a non-redirecting client. On .NET, each client owns an isolated connection
    /// pool so a connection opened by an explicitly trusted policy cannot be reused by a
    /// stricter plugin.
    /// </summary>
    public static HttpClient CreateHttpClient()
    {
#if NET
        return new HttpClient(new ValidatedAddressHandler());
#else
        return HttpClientProvider.GetNonRedirectingHttpClient();
#endif
    }

#if NET
    /// <summary>
    /// Keeps pinned operations from reusing unchecked connections opened for document loading or explicit policy bypasses.
    /// </summary>
    private sealed class ValidatedAddressHandler : HttpMessageHandler
    {
        private readonly HttpMessageInvoker _pinnedClient;
        private readonly HttpMessageInvoker _unpinnedClient;

        public ValidatedAddressHandler()
        {
            // Share cookies, not sockets, to preserve sessions between document loading and operations.
            var cookies = new CookieContainer();
            this._pinnedClient = new HttpMessageInvoker(CreateHandler(cookies));
            this._unpinnedClient = new HttpMessageInvoker(CreateHandler(cookies));
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Reused connections skip ConnectCallback, so pinned requests must never use the unchecked pool.
            var client = request.Options.TryGetValue(ValidatedAddressesKey, out var addresses) && addresses.Length > 0
                ? this._pinnedClient
                : this._unpinnedClient;
            return client.SendAsync(request, cancellationToken);
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                this._pinnedClient.Dispose();
                this._unpinnedClient.Dispose();
            }
            base.Dispose(disposing);
        }

        private static SocketsHttpHandler CreateHandler(CookieContainer cookies)
        {
            return new SocketsHttpHandler
            {
                AllowAutoRedirect = false,
                CookieContainer = cookies,
                PooledConnectionLifetime = TimeSpan.FromMinutes(2),
                SslOptions = new SslClientAuthenticationOptions
                {
                    CertificateRevocationCheckMode = X509RevocationMode.Online,
                },
                ConnectCallback = ConnectAsync,
            };
        }
    }

    /// <summary>
    /// Connects directly to an address validated for the request, preventing a second DNS lookup from selecting a different destination.
    /// </summary>
    /// <remarks>
    /// For example, <c>https://api.example.com</c> can connect to validated address <c>93.184.216.34</c>
    /// while retaining the hostname for TLS and HTTP. Proxy destinations are left unchanged because the proxy owns DNS resolution.
    /// </remarks>
    private static async ValueTask<Stream> ConnectAsync(SocketsHttpConnectionContext context, CancellationToken cancellationToken)
    {
        var request = context.InitialRequestMessage;
        var destination = context.DnsEndPoint;

        // Pin only direct requests with vetted DNS results; proxies and explicit validation bypasses keep their normal routing.
        if (request.RequestUri is null ||
            !string.Equals(request.RequestUri.IdnHost, destination.Host, StringComparison.OrdinalIgnoreCase) ||
            request.RequestUri.Port != destination.Port ||
            !request.Options.TryGetValue(ValidatedAddressesKey, out var validatedAddresses) ||
            validatedAddresses.Length == 0)
        {
            return await ConnectSocketAsync(destination, cancellationToken).ConfigureAwait(false);
        }

        // Preserve resolver order and fall back only while no connection has been established.
        for (int i = 0; i < validatedAddresses.Length - 1; i++)
        {
            try
            {
                return await ConnectSocketAsync(new IPEndPoint(validatedAddresses[i], destination.Port), cancellationToken).ConfigureAwait(false);
            }
            catch (SocketException)
            {
                // Try the next vetted address.
            }
        }

        // Let the final connection failure propagate to the caller.
        return await ConnectSocketAsync(new IPEndPoint(validatedAddresses[^1], destination.Port), cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Opens a TCP stream to the exact endpoint. Passing an <see cref="IPEndPoint"/> avoids another DNS lookup.
    /// </summary>
    private static async ValueTask<Stream> ConnectSocketAsync(EndPoint endpoint, CancellationToken cancellationToken)
    {
        var socket = new Socket(SocketType.Stream, ProtocolType.Tcp) { NoDelay = true };
        try
        {
            await socket.ConnectAsync(endpoint, cancellationToken).ConfigureAwait(false);
            return new NetworkStream(socket, ownsSocket: true);
        }
        catch
        {
            socket.Dispose();
            throw;
        }
    }
#endif
}
