// Copyright (c) Microsoft. All rights reserved.

using System;
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
