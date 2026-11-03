// Copyright (c) Microsoft. All rights reserved.

using System;
#if NET
using System.Collections.Generic;
#endif
using System.Diagnostics.CodeAnalysis;
#if NET
using System.IO;
using System.Linq;
using System.Net;
#endif
using System.Net.Http;
#if NET
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Cryptography.X509Certificates;
using System.Threading;
using System.Threading.Tasks;
#endif
using Microsoft.Extensions.DependencyInjection;

#pragma warning disable CA2000 // Dispose objects before losing scope
#pragma warning disable CA2215 // Dispose methods should call base class dispose

namespace Microsoft.SemanticKernel.Http;

/// <summary>
/// Provides functionality for retrieving instances of HttpClient.
/// </summary>
[ExcludeFromCodeCoverage]
internal static class HttpClientProvider
{
#if NET
    internal static readonly HttpRequestOptionsKey<IPAddress[]> ValidatedAddressesKey = new("ValidatedAddresses");

    // RFC 8305's 250 ms delay starts another route (e.g., IPv4) without timing out the first (e.g., IPv6).
    private static readonly TimeSpan s_connectionAttemptDelay = TimeSpan.FromMilliseconds(250);
#endif

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient() => new(NonDisposableHttpClientHandler.Instance, disposeHandler: false);

    /// <summary>
    /// Retrieves an instance of HttpClient that does not automatically follow HTTP redirects.
    /// </summary>
    /// <returns>An instance of HttpClient that does not follow redirects.</returns>
    public static HttpClient GetNonRedirectingHttpClient() => new(NonDisposableHttpClientHandler.NonRedirectingInstance, disposeHandler: false);

    /// <summary>
    /// Retrieves a non-redirecting client that binds connections to validated addresses supplied on each request.
    /// </summary>
    /// <returns>An instance of HttpClient that does not follow redirects.</returns>
    public static HttpClient GetValidatedNonRedirectingHttpClient()
    {
#if NET
        return new HttpClient(ValidatedAddressHandler.Instance, disposeHandler: false);
#else
        return GetNonRedirectingHttpClient();
#endif
    }

#if NET
    internal static HttpClient GetValidatedNonRedirectingHttpClient(IWebProxy proxy) =>
        new(new ValidatedAddressHandler(proxy), disposeHandler: true);
#endif

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(HttpClient? httpClient = null) => httpClient ?? GetHttpClient();

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(IServiceProvider? serviceProvider = null) => GetHttpClient(serviceProvider?.GetService<HttpClient>());

    /// <summary>
    /// Retrieves an instance of HttpClient.
    /// </summary>
    /// <returns>An instance of HttpClient.</returns>
    public static HttpClient GetHttpClient(HttpClient? httpClient, IServiceProvider serviceProvider) => httpClient ?? GetHttpClient(serviceProvider?.GetService<HttpClient>());

#if NET
    /// <summary>
    /// Keeps validated requests from reusing unchecked connections opened when validation was explicitly bypassed.
    /// </summary>
    private sealed class ValidatedAddressHandler : HttpMessageHandler
    {
        public static ValidatedAddressHandler Instance { get; } = new();

        private readonly HttpMessageInvoker _validatedClient;
        private readonly HttpMessageInvoker _uncheckedClient;

        internal ValidatedAddressHandler(IWebProxy? proxy = null)
        {
            // Share cookies, not sockets, so changing validation policy cannot reuse a connection from another policy.
            var cookies = new CookieContainer();
            // A proxy owns destination resolution, so validated requests must connect directly to preserve address binding.
            this._validatedClient = new HttpMessageInvoker(CreateHandler(cookies, proxy: null, useProxy: false));
            this._uncheckedClient = new HttpMessageInvoker(CreateHandler(cookies, proxy, useProxy: true));
        }

        protected override Task<HttpResponseMessage> SendAsync(HttpRequestMessage request, CancellationToken cancellationToken)
        {
            // Reused connections skip ConnectCallback, so validated requests must use their own pool.
            var client = request.Options.TryGetValue(ValidatedAddressesKey, out var addresses) && addresses.Length > 0
                ? this._validatedClient
                : this._uncheckedClient;
            return client.SendAsync(request, cancellationToken);
        }

        protected override void Dispose(bool disposing)
        {
            if (disposing)
            {
                this._validatedClient.Dispose();
                this._uncheckedClient.Dispose();
            }
            base.Dispose(disposing);
        }

        private static SocketsHttpHandler CreateHandler(CookieContainer cookies, IWebProxy? proxy, bool useProxy)
        {
            return new SocketsHttpHandler
            {
                AllowAutoRedirect = false,
                CookieContainer = cookies,
                Proxy = proxy,
                PooledConnectionLifetime = TimeSpan.FromMinutes(2),
                UseProxy = useProxy,
                SslOptions = new SslClientAuthenticationOptions
                {
                    CertificateRevocationCheckMode = X509RevocationMode.Online,
                },
                ConnectCallback = ConnectAsync,
            };
        }
    }

    /// <summary>
    /// Connects directly to an address validated for the request while preserving the original hostname.
    /// </summary>
    private static async ValueTask<Stream> ConnectAsync(SocketsHttpConnectionContext context, CancellationToken cancellationToken)
    {
        var request = context.InitialRequestMessage;
        var destination = context.DnsEndPoint;

        // Pin only direct requests with vetted DNS results; explicit validation bypasses keep normal routing.
        if (request.RequestUri is null ||
            !string.Equals(request.RequestUri.IdnHost, destination.Host, StringComparison.OrdinalIgnoreCase) ||
            request.RequestUri.Port != destination.Port ||
            !request.Options.TryGetValue(ValidatedAddressesKey, out var validatedAddresses) ||
            validatedAddresses.Length == 0)
        {
            return await ConnectSocketAsync(destination, cancellationToken).ConfigureAwait(false);
        }

        return await ConnectToValidatedAddressesAsync(validatedAddresses, destination.Port, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Staggers connections to vetted addresses and disposes losing connections before returning the first success.
    /// </summary>
    private static async ValueTask<Stream> ConnectToValidatedAddressesAsync(IPAddress[] addresses, int port, CancellationToken cancellationToken)
    {
        if (addresses.Length == 1)
        {
            return await ConnectSocketAsync(new IPEndPoint(addresses[0], port), cancellationToken).ConfigureAwait(false);
        }

        // A winner can cancel the losers without cancelling the caller; caller cancellation still stops the race.
        using var raceCancellationSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
        var attempts = new List<Task<Stream>>(addresses.Length);
        var nextAttemptDelay = Task.CompletedTask;
        int nextAddress = 0;
        Stream? winningStream = null;

        try
        {
            while (true)
            {
                cancellationToken.ThrowIfCancellationRequested();

                // Start another route after a short delay, or immediately after all current routes fail.
                if (nextAddress < addresses.Length && (attempts.Count == 0 || nextAttemptDelay.IsCompleted))
                {
                    attempts.Add(ConnectSocketAsync(new IPEndPoint(addresses[nextAddress++], port), raceCancellationSource.Token).AsTask());
                    nextAttemptDelay = Task.Delay(s_connectionAttemptDelay, raceCancellationSource.Token);
                }

                IEnumerable<Task> candidates = attempts;
                if (nextAddress < addresses.Length)
                {
                    candidates = candidates.Append(nextAttemptDelay);
                }

                var completed = await Task.WhenAny(candidates).ConfigureAwait(false);
                if (ReferenceEquals(completed, nextAttemptDelay))
                {
                    continue;
                }

                var completedAttempt = attempts.First(attempt => ReferenceEquals(attempt, completed));
                try
                {
                    var stream = await completedAttempt.ConfigureAwait(false);
                    cancellationToken.ThrowIfCancellationRequested();
                    winningStream = stream;
                    return stream;
                }
                catch (SocketException) when (attempts.Count > 1 || nextAddress < addresses.Length)
                {
                    // A refused route must not abort another pending or untried address.
                    attempts.Remove(completedAttempt);
                    cancellationToken.ThrowIfCancellationRequested();
                }
            }
        }
        finally
        {
            raceCancellationSource.Cancel();
            try
            {
                await DisposeLosingConnectionsAsync(attempts, winningStream).ConfigureAwait(false);
            }
            catch
            {
                winningStream?.Dispose();
                throw;
            }
        }
    }

    /// <summary>
    /// Observes stopped attempts and closes every successful connection except the selected winner.
    /// </summary>
    private static async Task DisposeLosingConnectionsAsync(List<Task<Stream>> attempts, Stream? winningStream)
    {
        var completion = Task.WhenAll(attempts);
        try
        {
            await completion.ConfigureAwait(false);
        }
        catch (SocketException) when (completion.Exception is { } failures)
        {
            if (failures.InnerExceptions.Any(static exception => exception is not SocketException))
            {
                throw failures;
            }
        }
        catch (OperationCanceledException) when (completion.IsCanceled)
        {
        }
        finally
        {
            foreach (var attempt in attempts)
            {
                if (attempt.IsCompletedSuccessfully)
                {
                    var stream = await attempt.ConfigureAwait(false);
                    if (!ReferenceEquals(stream, winningStream))
                    {
                        stream.Dispose();
                    }
                }
            }
        }
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

    /// <summary>
    /// Represents a singleton implementation of <see cref="HttpClientHandler"/> that is not disposable.
    /// </summary>
    private sealed class NonDisposableHttpClientHandler : DelegatingHandler
    {
        /// <summary>
        /// Private constructor to prevent direct instantiation of the class.
        /// </summary>
        private NonDisposableHttpClientHandler(bool allowRedirect) : base(CreateHandler(allowRedirect))
        {
        }

        /// <summary>
        /// Gets the singleton instance of <see cref="NonDisposableHttpClientHandler"/> that follows HTTP redirects.
        /// </summary>
        public static NonDisposableHttpClientHandler Instance { get; } = new(allowRedirect: true);

        /// <summary>
        /// Gets the singleton instance of <see cref="NonDisposableHttpClientHandler"/> that does not follow HTTP redirects.
        /// </summary>
        public static NonDisposableHttpClientHandler NonRedirectingInstance { get; } = new(allowRedirect: false);

        /// <summary>
        /// Disposes the underlying resources held by the <see cref="NonDisposableHttpClientHandler"/>.
        /// This implementation does nothing to prevent unintended disposal, as it may affect all references.
        /// </summary>
        /// <param name="disposing">True if called from <see cref="Dispose"/>, false if called from a finalizer.</param>
        protected override void Dispose(bool disposing)
        {
            // Do nothing if called explicitly from Dispose, as it may unintentionally affect all references.
            // The base.Dispose(disposing) is not called to avoid invoking the disposal of HttpClientHandler resources.
            // This implementation assumes that the HttpMessageHandler is being used as a singleton and should not be disposed directly.
        }

#if NET
        private static SocketsHttpHandler CreateHandler(bool allowRedirect)
        {
            return new SocketsHttpHandler()
            {
                // Limit the lifetime of connections to better respect any DNS changes
                PooledConnectionLifetime = TimeSpan.FromMinutes(2),

                // Check cert revocation
                SslOptions = new SslClientAuthenticationOptions()
                {
                    CertificateRevocationCheckMode = X509RevocationMode.Online,
                },
                AllowAutoRedirect = allowRedirect,
            };
        }
#elif NETSTANDARD2_0_OR_GREATER
        private static HttpClientHandler CreateHandler(bool allowRedirect)
        {
            var handler = new HttpClientHandler() { AllowAutoRedirect = allowRedirect };
            try
            {
                handler.CheckCertificateRevocationList = true;
            }
            catch (PlatformNotSupportedException) { } // not supported on older frameworks
            return handler;
        }
#elif NETFRAMEWORK
        private static HttpClientHandler CreateHandler(bool allowRedirect)
            => new() { AllowAutoRedirect = allowRedirect };
#endif
    }
}
