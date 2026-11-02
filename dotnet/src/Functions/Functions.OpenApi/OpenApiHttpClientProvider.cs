// Copyright (c) Microsoft. All rights reserved.

#if NET
using System;
using System.Collections.Generic;
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
#else
using Microsoft.SemanticKernel.Http;
#endif

#pragma warning disable CA2000 // Ownership is transferred to the shared handler or NetworkStream.

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Creates the built-in OpenAPI HTTP client and binds validated DNS addresses to its connections.
/// </summary>
internal static class OpenApiHttpClientProvider
{
#if NET
    internal static readonly HttpRequestOptionsKey<IPAddress[]> ValidatedAddressesKey = new("OpenApiValidatedAddresses");

    // RFC 8305's 250 ms delay starts another route (e.g., IPv4) without timing out the first (e.g., IPv6).
    private static readonly TimeSpan s_connectionAttemptDelay = TimeSpan.FromMilliseconds(250);
#endif

    /// <summary>
    /// Creates a non-redirecting client backed by a shared handler with separate pinned and unchecked connection pools.
    /// </summary>
    public static HttpClient CreateHttpClient()
    {
#if NET
        return new HttpClient(ValidatedAddressHandler.Instance, disposeHandler: false);
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
        // Plugins have no disposal contract; keep pool ownership at assembly scope rather than allocating pools per plugin.
        public static ValidatedAddressHandler Instance { get; } = new();

        private readonly HttpMessageInvoker _pinnedClient;
        private readonly HttpMessageInvoker _unpinnedClient;

        private ValidatedAddressHandler()
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
    /// Address attempts overlap after a short delay, keeping slow routes viable until another address connects.
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

        return await ConnectToValidatedAddressesAsync(validatedAddresses, destination.Port, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Staggers connections to vetted addresses and disposes losing connections before returning the first success.
    /// </summary>
    /// <remarks>
    /// For example, IPv4 can start while IPv6 is pending, and either can still win.
    /// Only TCP connections are raced; HTTP uses the selected connection afterward.
    /// </remarks>
    private static async ValueTask<Stream> ConnectToValidatedAddressesAsync(IPAddress[] addresses, int port, CancellationToken cancellationToken)
    {
        if (addresses.Length == 1)
        {
            // With no alternative address, racing would only add bookkeeping.
            return await ConnectSocketAsync(new IPEndPoint(addresses[0], port), cancellationToken).ConfigureAwait(false);
        }

        // A winner can cancel the losers without cancelling the caller; caller cancellation still stops the race.
        using var raceCancellationSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);

        // Keep successes tracked: two addresses may connect before either is selected.
        var attempts = new List<Task<Stream>>(addresses.Length);
        var nextAttemptDelay = Task.CompletedTask;
        int nextAddress = 0;
        Stream? winningStream = null;

        try
        {
            while (true)
            {
                cancellationToken.ThrowIfCancellationRequested();

                // Start the next route while this one waits, or immediately if all earlier routes failed.
                if (nextAddress < addresses.Length && (attempts.Count == 0 || nextAttemptDelay.IsCompleted))
                {
                    // AsTask lets both the race and cleanup safely await the same connection result.
                    attempts.Add(ConnectSocketAsync(new IPEndPoint(addresses[nextAddress++], port), raceCancellationSource.Token).AsTask());
                    nextAttemptDelay = Task.Delay(s_connectionAttemptDelay, raceCancellationSource.Token);
                }

                IEnumerable<Task> candidates = attempts;
                // Include the delay only while another address can be started.
                // Otherwise, an expired delay makes WhenAny return immediately instead of waiting for a connection.
                if (nextAddress < addresses.Length)
                {
                    candidates = candidates.Append(nextAttemptDelay);
                }

                // Wait for either a connection attempt or the delay task to finish.
                // WhenAny returns the finished task itself, so we can identify which kind of event occurred.
                var completed = await Task.WhenAny(candidates).ConfigureAwait(false);
                if (ReferenceEquals(completed, nextAttemptDelay))
                {
                    // The timer is a launch signal, not an address timeout.
                    // The next iteration starts B without cancelling A, or stops if the caller cancelled.
                    continue;
                }

                // WhenAny reports completion, not success; await the connection below to observe its errors.
                var completedAttempt = attempts.First(attempt => ReferenceEquals(attempt, completed));
                try
                {
                    var stream = await completedAttempt.ConfigureAwait(false);

                    // If cancellation wins this race, leave the stream tracked so cleanup closes it.
                    cancellationToken.ThrowIfCancellationRequested();

                    winningStream = stream;

                    return stream;
                }
                // The failed task is still counted; require another attempt or untried address before ignoring its error.
                catch (SocketException) when (attempts.Count > 1 || nextAddress < addresses.Length)
                {
                    // E.g., a refused IPv4 route must not abort a still-pending IPv6 connection.
                    attempts.Remove(completedAttempt);
                    cancellationToken.ThrowIfCancellationRequested();
                }
            }
        }
        finally
        {
            // Even return must finish cleanup before transferring ownership of the winning stream.
            raceCancellationSource.Cancel();
            try
            {
                await DisposeLosingConnectionsAsync(attempts, winningStream).ConfigureAwait(false);
            }
            catch
            {
                // A cleanup failure prevents ownership transfer, even if a connection succeeded.
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
            // Refused routes are expected; unrelated failures must not turn into a successful request.
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
            // IPv4 and IPv6 can both connect before selection; cancellation alone does not close either stream.
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
}
