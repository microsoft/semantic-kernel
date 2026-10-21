// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Security;
using System.Net.Sockets;
using System.Security.Authentication;
using System.Security.Cryptography;
using System.Security.Cryptography.X509Certificates;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.OpenApi;
using Xunit;

#pragma warning disable CA2000 // TcpListener is stopped in the finally block.

namespace SemanticKernel.Functions.UnitTests.OpenApi;

public sealed class OpenApiHttpClientProviderTests
{
    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ItShouldConnectToValidatedAddressWithoutChangingHostAsync(bool useFallback)
    {
        // Arrange
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var listener = new TcpListener(IPAddress.Parse("127.0.0.2"), 0);
        listener.Start();

        try
        {
            var endpoint = Assert.IsType<IPEndPoint>(listener.LocalEndpoint);
            var serverTask = ServeOneRequestAsync(listener, cancellationTokenSource.Token);
            using var client = OpenApiHttpClientProvider.CreateHttpClient();
            using var request = new HttpRequestMessage(
                HttpMethod.Get,
                $"http://localhost:{endpoint.Port}/resource");
            request.Options.Set(
                OpenApiHttpClientProvider.ValidatedAddressesKey,
                useFallback ? [IPAddress.Parse("127.0.0.3"), endpoint.Address] : [endpoint.Address]);

            // Act
            using var response = await client.SendAsync(request, cancellationTokenSource.Token);
            var (requestLine, hostHeader) = await serverTask;

            // Assert
            response.EnsureSuccessStatusCode();
            Assert.Equal("GET /resource HTTP/1.1", requestLine);
            Assert.Equal($"Host: localhost:{endpoint.Port}", hostHeader);
        }
        finally
        {
            listener.Stop();
        }
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ItShouldHandleAStalledValidatedAddressAsync(bool cancelRequest)
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(15));
        var stalledListener = new TcpListener(IPAddress.Parse("127.0.0.3"), 0);
        TcpListener? reachableListener = null;
        var backlogConnections = new List<Socket>();
        stalledListener.Start(1);

        try
        {
            var endpoint = Assert.IsType<IPEndPoint>(stalledListener.LocalEndpoint);
            reachableListener = new TcpListener(IPAddress.Parse("127.0.0.2"), endpoint.Port);
            reachableListener.Start();

            // A full listen backlog stalls new connection attempts instead of immediately refusing them.
            await FillListenBacklogAsync(stalledListener, backlogConnections, cancellationTokenSource.Token);
            using var client = OpenApiHttpClientProvider.CreateHttpClient();
            client.Timeout = TimeSpan.FromMilliseconds(1500);
            using var request = new HttpRequestMessage(HttpMethod.Get, $"http://localhost:{endpoint.Port}/resource");
            request.Options.Set(OpenApiHttpClientProvider.ValidatedAddressesKey, [IPAddress.Parse("127.0.0.3"), IPAddress.Parse("127.0.0.2")]);

            if (cancelRequest)
            {
                using var requestCancellationSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationTokenSource.Token);
                requestCancellationSource.CancelAfter(TimeSpan.FromMilliseconds(100));

                await Assert.ThrowsAnyAsync<OperationCanceledException>(() => client.SendAsync(request, requestCancellationSource.Token));
                Assert.False(reachableListener.Pending());
            }
            else
            {
                var serverTask = ServeOneRequestAsync(reachableListener, cancellationTokenSource.Token);
                using var response = await client.SendAsync(request, cancellationTokenSource.Token);
                response.EnsureSuccessStatusCode();
                var (requestLine, hostHeader) = await serverTask;

                Assert.Equal("GET /resource HTTP/1.1", requestLine);
                Assert.Equal($"Host: localhost:{endpoint.Port}", hostHeader);
                await DrainListenBacklogAsync(stalledListener, backlogConnections, cancellationTokenSource.Token);
                Assert.False(stalledListener.Pending());
            }
        }
        finally
        {
            cancellationTokenSource.Cancel();
            stalledListener.Stop();
            reachableListener?.Stop();
            foreach (var socket in backlogConnections)
            {
                socket.Dispose();
            }
        }
    }

    [Fact]
    public async Task ItShouldKeepAnEarlierValidatedAddressAttemptAliveAsync()
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var listener = new TcpListener(IPAddress.Parse("127.0.0.3"), 0);
        var backlogConnections = new List<Socket>();
        Task<(string? RequestLine, string? HostHeader)>? serverTask = null;
        listener.Start(1);

        try
        {
            var endpoint = Assert.IsType<IPEndPoint>(listener.LocalEndpoint);
            await FillListenBacklogAsync(listener, backlogConnections, cancellationTokenSource.Token);
            serverTask = ServeAfterReleasingBacklogAsync(listener, backlogConnections, cancellationTokenSource.Token);
            using var client = OpenApiHttpClientProvider.CreateHttpClient();
            client.Timeout = TimeSpan.FromSeconds(5);
            using var request = new HttpRequestMessage(HttpMethod.Get, $"http://localhost:{endpoint.Port}/resource");
            request.Options.Set(OpenApiHttpClientProvider.ValidatedAddressesKey, [endpoint.Address, IPAddress.Parse("127.0.0.2")]);

            using var response = await client.SendAsync(request, cancellationTokenSource.Token);
            response.EnsureSuccessStatusCode();
            var (requestLine, hostHeader) = await serverTask;

            Assert.Equal("GET /resource HTTP/1.1", requestLine);
            Assert.Equal($"Host: localhost:{endpoint.Port}", hostHeader);
        }
        finally
        {
            cancellationTokenSource.Cancel();
            listener.Stop();
            foreach (var socket in backlogConnections)
            {
                socket.Dispose();
            }
            if (serverTask is not null)
            {
                try
                {
                    await serverTask;
                }
                catch (OperationCanceledException) when (cancellationTokenSource.IsCancellationRequested)
                {
                }
                catch (SocketException) when (cancellationTokenSource.IsCancellationRequested)
                {
                }
            }
        }
    }

    [Fact]
    public async Task ItShouldPropagateFailureWhenAllValidatedAddressesFailAsync()
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        using var socket = new Socket(AddressFamily.InterNetwork, SocketType.Stream, ProtocolType.Tcp);
        socket.Bind(new IPEndPoint(IPAddress.Parse("127.0.0.2"), 0));
        var endpoint = Assert.IsType<IPEndPoint>(socket.LocalEndPoint);
        using var client = OpenApiHttpClientProvider.CreateHttpClient();
        using var request = new HttpRequestMessage(HttpMethod.Get, $"http://localhost:{endpoint.Port}/resource");
        request.Options.Set(OpenApiHttpClientProvider.ValidatedAddressesKey, [endpoint.Address, IPAddress.Parse("127.0.0.3")]);

        var exception = await Assert.ThrowsAsync<HttpRequestException>(() => client.SendAsync(request, cancellationTokenSource.Token));

        Assert.IsType<SocketException>(exception.InnerException);
    }

    [Fact]
    public async Task ItShouldNotReuseAnUncheckedConnectionForAPinnedRequestAsync()
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var uncheckedListener = new TcpListener(IPAddress.Loopback, 0);
        uncheckedListener.Start();
        var endpoint = Assert.IsType<IPEndPoint>(uncheckedListener.LocalEndpoint);
        var pinnedListener = new TcpListener(IPAddress.Parse("127.0.0.2"), endpoint.Port);
        var releaseConnection = new TaskCompletionSource(TaskCreationOptions.RunContinuationsAsynchronously);
        Task<(string? RequestLine, string? HostHeader)>? uncheckedServerTask = null;

        try
        {
            pinnedListener.Start();
            uncheckedServerTask = ServeOneRequestAsync(
                uncheckedListener, cancellationTokenSource.Token, releaseConnection.Task);
            var pinnedServerTask = ServeOneRequestAsync(pinnedListener, cancellationTokenSource.Token);
            using var client = OpenApiHttpClientProvider.CreateHttpClient();
            var uri = new Uri($"http://localhost:{endpoint.Port}/resource");

            // Keep the unchecked document-loading connection available in its pool.
            using var documentResponse = await client.GetAsync(uri, cancellationTokenSource.Token);
            documentResponse.EnsureSuccessStatusCode();
            Assert.False(uncheckedServerTask.IsCompleted);

            using var request = new HttpRequestMessage(HttpMethod.Get, uri);
            request.Options.Set(OpenApiHttpClientProvider.ValidatedAddressesKey, [IPAddress.Parse("127.0.0.2")]);
            using var response = await client.SendAsync(request, cancellationTokenSource.Token);
            response.EnsureSuccessStatusCode();
            var (requestLine, hostHeader) = await pinnedServerTask;

            Assert.Equal("GET /resource HTTP/1.1", requestLine);
            Assert.Equal($"Host: localhost:{endpoint.Port}", hostHeader);
        }
        finally
        {
            releaseConnection.TrySetResult();
            cancellationTokenSource.Cancel();
            uncheckedListener.Stop();
            pinnedListener.Stop();
            if (uncheckedServerTask is not null)
            {
                try
                {
                    await uncheckedServerTask;
                }
                catch (OperationCanceledException) when (cancellationTokenSource.IsCancellationRequested)
                {
                }
                catch (SocketException) when (cancellationTokenSource.IsCancellationRequested)
                {
                }
            }
        }
    }

    [Fact]
    public async Task ItShouldPreserveTlsHostnameAndRejectUntrustedCertificatesAsync()
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        using var key = RSA.Create(2048);
        var certificateRequest = new CertificateRequest(
            "CN=localhost", key, HashAlgorithmName.SHA256, RSASignaturePadding.Pkcs1);
        using var certificate = certificateRequest.CreateSelfSigned(
            DateTimeOffset.UtcNow.AddMinutes(-1), DateTimeOffset.UtcNow.AddMinutes(5));
        var listener = new TcpListener(IPAddress.Parse("127.0.0.2"), 0);
        listener.Start();

        try
        {
            var endpoint = Assert.IsType<IPEndPoint>(listener.LocalEndpoint);
            var serverTask = CaptureTlsHostnameAsync(listener, certificate, cancellationTokenSource.Token);
            using var client = OpenApiHttpClientProvider.CreateHttpClient();
            using var request = new HttpRequestMessage(HttpMethod.Get, $"https://localhost:{endpoint.Port}/resource");
            request.Options.Set(OpenApiHttpClientProvider.ValidatedAddressesKey, [endpoint.Address]);

            await Assert.ThrowsAsync<HttpRequestException>(() => client.SendAsync(request, cancellationTokenSource.Token));
            Assert.Equal("localhost", await serverTask);
        }
        finally
        {
            listener.Stop();
        }
    }

    [Fact]
    public void ItShouldPreserveCallerSuppliedClients()
    {
        using var client = new HttpClient();

        Assert.Same(client, OpenApiKernelPluginFactory.GetHttpClient(client));
    }

    [Theory]
    [InlineData(false)]
    [InlineData(true)]
    public async Task ItShouldReuseTheSharedPoolAfterDisposingAClientAsync(bool pinAddress)
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var address = pinAddress ? IPAddress.Parse("127.0.0.2") : IPAddress.Loopback;
        var listener = new TcpListener(address, 0);
        listener.Start();

        try
        {
            var endpoint = Assert.IsType<IPEndPoint>(listener.LocalEndpoint);
            var serverTask = ServeTwoRequestsOnOneConnectionAsync(listener, cancellationTokenSource.Token);
            var uri = new Uri($"http://localhost:{endpoint.Port}/resource");

            // Disposing a lightweight client must not close the shared pool's connection.
            for (int i = 0; i < 2; i++)
            {
                using var client = OpenApiHttpClientProvider.CreateHttpClient();
                using var request = new HttpRequestMessage(HttpMethod.Get, uri);
                if (pinAddress)
                {
                    request.Options.Set(OpenApiHttpClientProvider.ValidatedAddressesKey, [address]);
                }

                using var response = await client.SendAsync(request, cancellationTokenSource.Token);
                response.EnsureSuccessStatusCode();
            }

            await serverTask;
        }
        finally
        {
            cancellationTokenSource.Cancel();
            listener.Stop();
        }
    }

    private static async Task FillListenBacklogAsync(TcpListener listener, List<Socket> connections, CancellationToken cancellationToken)
    {
        for (int i = 0; i < 10; i++)
        {
            var socket = new Socket(SocketType.Stream, ProtocolType.Tcp);
            connections.Add(socket);
            using var attemptCancellationSource = CancellationTokenSource.CreateLinkedTokenSource(cancellationToken);
            attemptCancellationSource.CancelAfter(TimeSpan.FromMilliseconds(500));

            try
            {
                await socket.ConnectAsync(listener.LocalEndpoint, attemptCancellationSource.Token);
            }
            catch (OperationCanceledException) when (!cancellationToken.IsCancellationRequested)
            {
                // On Linux, a cancelled probe can still connect later and be mistaken for the HTTP client.
                socket.Dispose();
                connections.Remove(socket);
                return;
            }
        }

        Assert.Fail("The loopback listener's backlog did not fill.");
    }

    private static async Task DrainListenBacklogAsync(TcpListener listener, List<Socket> connections, CancellationToken cancellationToken)
    {
        foreach (var socket in connections)
        {
            if (socket.Connected)
            {
                using var connection = await listener.AcceptTcpClientAsync(cancellationToken);
            }
        }
    }

    private static async Task<(string? RequestLine, string? HostHeader)> ServeAfterReleasingBacklogAsync(TcpListener listener, List<Socket> connections, CancellationToken cancellationToken)
    {
        // Release this route late to verify that starting another attempt does not cancel it.
        await Task.Delay(TimeSpan.FromMilliseconds(1250), cancellationToken);
        await DrainListenBacklogAsync(listener, connections, cancellationToken);
        return await ServeOneRequestAsync(listener, cancellationToken);
    }

    private static async Task ServeTwoRequestsOnOneConnectionAsync(TcpListener listener, CancellationToken cancellationToken)
    {
        using var client = await listener.AcceptTcpClientAsync(cancellationToken);
        await using var stream = client.GetStream();
        using var reader = new StreamReader(stream, Encoding.ASCII, detectEncodingFromByteOrderMarks: false, leaveOpen: true);

        for (int i = 0; i < 2; i++)
        {
            Assert.Equal("GET /resource HTTP/1.1", await reader.ReadLineAsync(cancellationToken));
            string? header;
            do
            {
                header = await reader.ReadLineAsync(cancellationToken);
            }
            while (!string.IsNullOrEmpty(header));

            var connectionHeader = i == 0 ? "keep-alive" : "close";
            var response = $"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: {connectionHeader}\r\n\r\n";
            await stream.WriteAsync(Encoding.ASCII.GetBytes(response), cancellationToken);
        }
    }

    private static async Task<(string? RequestLine, string? HostHeader)> ServeOneRequestAsync(
        TcpListener listener,
        CancellationToken cancellationToken,
        Task? releaseConnection = null)
    {
        using var client = await listener.AcceptTcpClientAsync(cancellationToken);
        await using var stream = client.GetStream();
        using var reader = new StreamReader(
            stream,
            Encoding.ASCII,
            detectEncodingFromByteOrderMarks: false,
            bufferSize: 1024,
            leaveOpen: true);

        var requestLine = await reader.ReadLineAsync(cancellationToken);
        string? hostHeader = null;
        string? header;
        do
        {
            header = await reader.ReadLineAsync(cancellationToken);
            if (header?.StartsWith("Host:", StringComparison.OrdinalIgnoreCase) == true)
            {
                hostHeader = header;
            }
        }
        while (!string.IsNullOrEmpty(header));

        var connectionHeader = releaseConnection is null ? "close" : "keep-alive";
        var response = $"HTTP/1.1 200 OK\r\nContent-Length: 0\r\nConnection: {connectionHeader}\r\n\r\n";
        await stream.WriteAsync(Encoding.ASCII.GetBytes(response), cancellationToken);
        if (releaseConnection is not null)
        {
            await releaseConnection.WaitAsync(cancellationToken);
        }
        return (requestLine, hostHeader);
    }

    private static async Task<string?> CaptureTlsHostnameAsync(
        TcpListener listener,
        X509Certificate2 certificate,
        CancellationToken cancellationToken)
    {
        using var client = await listener.AcceptTcpClientAsync(cancellationToken);
        await using var stream = new SslStream(client.GetStream());
        string? tlsHostname = null;
        try
        {
            await stream.AuthenticateAsServerAsync(new SslServerAuthenticationOptions
            {
                ServerCertificateSelectionCallback = (_, hostname) =>
                {
                    tlsHostname = hostname;
                    return certificate;
                }
            }, cancellationToken);
        }
        catch (AuthenticationException)
        {
            // The client must reject the self-signed certificate after sending its original SNI hostname.
        }
        catch (IOException)
        {
            // Some TLS providers close the stream when rejecting the certificate.
        }
        return tlsHostname;
    }
}
