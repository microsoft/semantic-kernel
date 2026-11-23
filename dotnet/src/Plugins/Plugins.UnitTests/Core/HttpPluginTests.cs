// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Plugins.Core;
using Moq;
using Moq.Protected;
using Xunit;

#pragma warning disable CA2000 // TcpListener is stopped in the finally block.

namespace SemanticKernel.Plugins.UnitTests.Core;

public sealed class HttpPluginTests : IDisposable
{
    private readonly string _content = "hello world";
    private readonly string _uriString = "http://1.1.1.1";

    private readonly HttpResponseMessage _response = new()
    {
        StatusCode = HttpStatusCode.OK,
        Content = new StringContent("hello world"),
    };

    [Fact]
    public void ItCanBeInstantiated()
    {
        // Act - Assert no exception occurs
        var plugin = new HttpPlugin();
    }

    [Fact]
    public void ItCanBeImported()
    {
        // Act - Assert no exception occurs e.g. due to reflection
        Assert.NotNull(KernelPluginFactory.CreateFromType<HttpPlugin>("http"));
    }

    [Fact]
    public async Task ItCanGetAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri(this._uriString)] };

        // Act
        var result = await plugin.GetAsync(this._uriString);

        // Assert
        Assert.Equal(this._content, result);
        this.VerifyMock(mockHandler, HttpMethod.Get);
    }

    [Fact]
    public async Task ItCanPostAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri(this._uriString)] };

        // Act
        var result = await plugin.PostAsync(this._uriString, this._content);

        // Assert
        Assert.Equal(this._content, result);
        this.VerifyMock(mockHandler, HttpMethod.Post);
    }

    [Fact]
    public async Task ItCanPutAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri(this._uriString)] };

        // Act
        var result = await plugin.PutAsync(this._uriString, this._content);

        // Assert
        Assert.Equal(this._content, result);
        this.VerifyMock(mockHandler, HttpMethod.Put);
    }

    [Fact]
    public async Task ItCanDeleteAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri(this._uriString)] };

        // Act
        var result = await plugin.DeleteAsync(this._uriString);

        // Assert
        Assert.Equal(this._content, result);
        this.VerifyMock(mockHandler, HttpMethod.Delete);
    }

    [Fact]
    public async Task ItDeniesAllOriginsWithDefaultConfigAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client);

        // Act & Assert - default config denies all origins
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.GetAsync(this._uriString));
    }

    [Fact]
    public async Task ItThrowsInvalidOperationExceptionForDisallowedOriginAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client)
        {
            AllowedOrigins = [new Uri("http://www.example.com")]
        };
        var invalidUri = "http://www.notexample.com";

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.GetAsync(invalidUri));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.PostAsync(invalidUri, this._content));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.PutAsync(invalidUri, this._content));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.DeleteAsync(invalidUri));
    }

    [Theory]
    [InlineData("https://api.example.com/resource", true)]
    [InlineData("HTTPS://API.EXAMPLE.COM:443/resource?value=test#fragment", true)]
    [InlineData("http://legacy.example.com:8080/file", true)]
    [InlineData("http://api.example.com/resource", false)]
    [InlineData("https://api.example.com:8443/resource", false)]
    [InlineData("http://api.example.com:8080/file", false)]
    [InlineData("https://legacy.example.com:8080/file", false)]
    [InlineData("https://other.example.com/resource", false)]
    [InlineData("https://sub.api.example.com/resource", false)]
    public async Task ItChecksExactOriginsAsync(string uri, bool isAllowed)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client)
        {
            AllowedOrigins = [new Uri("https://api.example.com"), new Uri("http://legacy.example.com:8080")],
            AllowPrivateNetworkAccess = true
        };

        if (isAllowed)
        {
            Assert.Equal(this._content, await plugin.GetAsync(uri));
            mockHandler.Protected().Verify(
                "SendAsync", Times.Once(),
                ItExpr.Is<HttpRequestMessage>(request => request.RequestUri == new Uri(uri)),
                ItExpr.IsAny<CancellationToken>());
        }
        else
        {
            await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync(uri));
            VerifyNoRequest(mockHandler);
        }
    }

    [Theory]
    [InlineData("GET")]
    [InlineData("POST")]
    [InlineData("PUT")]
    [InlineData("DELETE")]
    public async Task ItEnforcesOriginsForAllHttpMethodsAsync(string method)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri("https://1.1.1.1")] };

        await Assert.ThrowsAsync<InvalidOperationException>(() => SendAsync(plugin, method, "http://1.1.1.1"));
        await Assert.ThrowsAsync<InvalidOperationException>(() => SendAsync(plugin, method, "https://1.1.1.1:8443"));
        VerifyNoRequest(mockHandler);

        Assert.Equal(this._content, await SendAsync(plugin, method, "https://1.1.1.1:443/resource"));
    }

    [Theory]
    [InlineData("http://1.1.1.1:8080/resource")]
    [InlineData("https://1.1.1.1:8443/resource")]
    public async Task ItDeniesEmptyAndNullOriginsAsync(string uri)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client)
        {
            AllowedOrigins = []
        };

        await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync(uri));
        VerifyNoRequest(mockHandler);

        plugin.AllowedOrigins = null;
        await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync(uri));
        VerifyNoRequest(mockHandler);
    }

    [Theory]
    [InlineData("http://1.1.1.1", "http://1.1.1.1:80/resource")]
    [InlineData("http://1.1.1.1:80", "http://1.1.1.1/resource")]
    [InlineData("https://1.1.1.1:443", "https://1.1.1.1/resource")]
    [InlineData("https://[2606:4700:4700::1111]", "https://[2606:4700:4700::1111]:443/resource")]
    public async Task ItMatchesDefaultPortsAndIpOriginsAsync(string origin, string uri)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri(origin)] };

        Assert.Equal(this._content, await plugin.GetAsync(uri));
    }

    [Theory]
    [InlineData("https://bücher.example", "https://xn--bcher-kva.example/resource")]
    [InlineData("https://xn--bcher-kva.example", "https://bücher.example/resource")]
    public async Task ItMatchesInternationalizedHostsByAsciiFormAsync(string origin, string uri)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri(origin)], AllowPrivateNetworkAccess = true };

        Assert.Equal(this._content, await plugin.GetAsync(uri));
    }

    [Fact]
    public async Task ItRejectsHostThatCannotBeConvertedToAsciiAsync()
    {
        // The label fits in the URI, but its ASCII form exceeds the DNS label limit.
        var uri = new Uri($"https://{new string('\u00fc', 59)}.example");
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri("https://1.1.1.1")] };

        var exception = Assert.Throws<ArgumentException>(() => plugin.AllowedOrigins = [uri]);
        Assert.Equal(nameof(HttpPlugin.AllowedOrigins), exception.ParamName);
        await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync(uri.AbsoluteUri));
        VerifyNoRequest(mockHandler);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("relative/path")]
    [InlineData("ftp://example.com")]
    [InlineData("https://user:password@example.com")]
    [InlineData("https://example.com/path")]
    [InlineData("https://example.com?query=value")]
    [InlineData("https://example.com#fragment")]
    public async Task ItRejectsInvalidOriginConfigurationWithoutChangingPolicyAsync(string? origin)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri("https://1.1.1.1")] };
        var invalidOrigin = origin is null ? null! : new Uri(origin, UriKind.RelativeOrAbsolute);

        var exception = Assert.Throws<ArgumentException>(
            () => plugin.AllowedOrigins = [new Uri("https://other.example.com"), invalidOrigin]);
        Assert.Equal(nameof(HttpPlugin.AllowedOrigins), exception.ParamName);

        Assert.Equal(this._content, await plugin.GetAsync("https://1.1.1.1/resource"));
        await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync("https://other.example.com"));
    }

    [Theory]
    [InlineData("http://127.0.0.1")]
    [InlineData("https://[::1]")]
    public async Task ItStillBlocksPrivateAddressesForAllowedOriginsAsync(string origin)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri(origin)] };

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync(origin));

        Assert.Contains("host resolves to", exception.Message, StringComparison.Ordinal);
        VerifyNoRequest(mockHandler);
    }

    [Fact]
    public async Task ItDoesNotFollowRedirectsAsync()
    {
        // Arrange - start a local server that always returns a 302 redirect
        await using var server = new RedirectLoopbackServer("secret", "text/plain", []);

        var plugin = new HttpPlugin()
        {
            AllowedOrigins = [new Uri(server.BaseUri.GetLeftPart(UriPartial.Authority))],
            AllowPrivateNetworkAccess = true
        };

        // Act & Assert - the plugin should throw because 302 is a non-success status
        await Assert.ThrowsAsync<HttpOperationException>(() => plugin.GetAsync(new Uri(server.BaseUri, "start").AbsoluteUri));
        Assert.False(server.RedirectTargetContacted, "The redirect target should not have been contacted.");
    }

    [Theory]
    [InlineData("GET")]
    [InlineData("POST")]
    [InlineData("PUT")]
    [InlineData("DELETE")]
    public async Task ItBlocksNonPublicAddressesBeforeSendingAsync(string method)
    {
        string[] addresses =
        [
            "169.254.169.254", "127.0.0.1", "10.0.0.1", "172.16.0.1", "192.168.0.1",
            "100.64.0.1", "0.0.0.0", "224.0.0.1", "198.18.0.1", "192.0.2.1",
            "::1", "fe80::1", "fec0::", "fec0::1", "feff:ffff:ffff:ffff:ffff:ffff:ffff:ffff",
            "fc00::1", "ff02::1", "::ffff:169.254.169.254"
        ];

        foreach (var address in addresses)
        {
            var mockHandler = this.CreateMock();
            using var client = new HttpClient(mockHandler.Object);
            var host = address.Contains(':') ? $"[{address}]" : address;
            var uri = new Uri($"http://{host}/");
            var plugin = new HttpPlugin(client) { AllowedOrigins = [uri] };

            var exception = await Assert.ThrowsAsync<InvalidOperationException>(
                () => SendAsync(plugin, method, uri.AbsoluteUri));

            Assert.Contains("host resolves to", exception.Message, StringComparison.Ordinal);
            Assert.Contains("AllowPrivateNetworkAccess", exception.Message, StringComparison.Ordinal);
            VerifyNoRequest(mockHandler);
        }
    }

    [Theory]
    [InlineData("1.1.1.1")]
    [InlineData("[2606:4700:4700::1111]")]
    public async Task ItAllowsPublicLiteralAddressesAsync(string address)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var uri = new Uri($"http://{address}/");
        var plugin = new HttpPlugin(client) { AllowedOrigins = [uri] };

        Assert.Equal(this._content, await plugin.GetAsync(uri.AbsoluteUri));
    }

    [Fact]
    public async Task ItPassesValidatedAddressesToTransportAsync()
    {
        // Arrange
        var validatedAddress = IPAddress.Parse("93.184.216.34");
        var mockHandler = this.CreateMock();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .Callback<HttpRequestMessage, CancellationToken>((request, _) =>
            {
                Assert.True(request.Options.TryGetValue(HttpClientProvider.ValidatedAddressesKey, out var addresses));
                Assert.Equal([validatedAddress], addresses);
            })
            .ReturnsAsync(this._response);
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(
            client,
            (_, _) => Task.FromResult(new[] { validatedAddress }),
            clientSupportsValidatedAddresses: true)
        {
            AllowedOrigins = [new Uri("http://example.test")]
        };

        // Act
        var result = await plugin.GetAsync("http://example.test/");

        // Assert
        Assert.Equal(this._content, result);
    }

    [Fact]
    public async Task ItRejectsCallerSuppliedClientWhenAddressBindingIsRequiredAsync()
    {
        var validatedAddress = IPAddress.Parse("93.184.216.34");
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(
            client,
            (_, _) => Task.FromResult(new[] { validatedAddress }))
        {
            AllowedOrigins = [new Uri("http://example.test")]
        };

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(
            () => plugin.GetAsync("http://example.test/"));

        Assert.Contains("built-in HTTP client", exception.Message, StringComparison.Ordinal);
        VerifyNoRequest(mockHandler);
    }

    [Fact]
    public async Task ItConnectsToValidatedAddressWithoutChangingHostAsync()
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var listener = new TcpListener(IPAddress.Parse("127.0.0.2"), 0);
        listener.Start();

        try
        {
            var endpoint = Assert.IsType<IPEndPoint>(listener.LocalEndpoint);
            var serverTask = ServeOneRequestAsync(listener, cancellationTokenSource.Token);
            using var client = HttpClientProvider.GetValidatedNonRedirectingHttpClient();
            using var request = new HttpRequestMessage(
                HttpMethod.Get,
                $"http://localhost:{endpoint.Port}/resource");
            request.Options.Set(HttpClientProvider.ValidatedAddressesKey, [endpoint.Address]);

            using var response = await client.SendAsync(request, cancellationTokenSource.Token);
            var (requestLine, hostHeader) = await serverTask;

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
    public async Task ItIgnoresConfiguredProxyForValidatedRequestsAsync()
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var targetListener = new TcpListener(IPAddress.Parse("127.0.0.2"), 0);
        var proxyListener = new TcpListener(IPAddress.Parse("127.0.0.3"), 0);
        targetListener.Start();
        proxyListener.Start();
        Task<(string? RequestLine, string? HostHeader)>? targetTask = null;
        Task<(string? RequestLine, string? HostHeader)>? proxyTask = null;

        try
        {
            var targetEndpoint = Assert.IsType<IPEndPoint>(targetListener.LocalEndpoint);
            var proxyEndpoint = Assert.IsType<IPEndPoint>(proxyListener.LocalEndpoint);
            targetTask = ServeOneRequestAsync(targetListener, cancellationTokenSource.Token, "target");
            proxyTask = ServeOneRequestAsync(proxyListener, cancellationTokenSource.Token, "proxy");
            using var client = HttpClientProvider.GetValidatedNonRedirectingHttpClient(
                new WebProxy($"http://{proxyEndpoint.Address}:{proxyEndpoint.Port}"));
            using var request = new HttpRequestMessage(
                HttpMethod.Get,
                $"http://example.test:{targetEndpoint.Port}/resource");
            request.Options.Set(HttpClientProvider.ValidatedAddressesKey, [targetEndpoint.Address]);

            using var response = await client.SendAsync(request, cancellationTokenSource.Token);

            Assert.Equal("target", await response.Content.ReadAsStringAsync(cancellationTokenSource.Token));
            Assert.True(targetTask.IsCompletedSuccessfully);
            Assert.False(proxyTask.IsCompleted);
        }
        finally
        {
            cancellationTokenSource.Cancel();
            targetListener.Stop();
            proxyListener.Stop();
            await ObserveServerTaskAsync(targetTask);
            await ObserveServerTaskAsync(proxyTask);
        }
    }

    [Fact]
    public async Task ItUsesConfiguredProxyForUncheckedRequestsAsync()
    {
        using var cancellationTokenSource = new CancellationTokenSource(TimeSpan.FromSeconds(10));
        var proxyListener = new TcpListener(IPAddress.Parse("127.0.0.3"), 0);
        proxyListener.Start();
        Task<(string? RequestLine, string? HostHeader)>? proxyTask = null;

        try
        {
            var proxyEndpoint = Assert.IsType<IPEndPoint>(proxyListener.LocalEndpoint);
            proxyTask = ServeOneRequestAsync(proxyListener, cancellationTokenSource.Token, "proxy");
            using var client = HttpClientProvider.GetValidatedNonRedirectingHttpClient(
                new WebProxy($"http://{proxyEndpoint.Address}:{proxyEndpoint.Port}"));
            using var request = new HttpRequestMessage(HttpMethod.Get, "http://example.test:8080/resource");

            using var response = await client.SendAsync(request, cancellationTokenSource.Token);
            var (requestLine, hostHeader) = await proxyTask;

            Assert.Equal("proxy", await response.Content.ReadAsStringAsync(cancellationTokenSource.Token));
            Assert.Equal("GET http://example.test:8080/resource HTTP/1.1", requestLine);
            Assert.Equal("Host: example.test:8080", hostHeader);
        }
        finally
        {
            cancellationTokenSource.Cancel();
            proxyListener.Stop();
            await ObserveServerTaskAsync(proxyTask);
        }
    }

    [Theory]
    [InlineData("GET", "127.0.0.1")]
    [InlineData("POST", "127.0.0.1")]
    [InlineData("PUT", "127.0.0.1")]
    [InlineData("DELETE", "127.0.0.1")]
    [InlineData("GET", "[fec0::1]")]
    [InlineData("POST", "[fec0::1]")]
    [InlineData("PUT", "[fec0::1]")]
    [InlineData("DELETE", "[fec0::1]")]
    [InlineData("GET", "unresolved.example.invalid")]
    [InlineData("POST", "unresolved.example.invalid")]
    [InlineData("PUT", "unresolved.example.invalid")]
    [InlineData("DELETE", "unresolved.example.invalid")]
    public async Task ItAllowsExplicitPrivateNetworkAccessAsync(string method, string host)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client)
        {
            AllowedOrigins = [new Uri($"http://{host}")],
            AllowPrivateNetworkAccess = true
        };

        Assert.Equal(this._content, await SendAsync(plugin, method, $"http://{host}/"));
    }

    [Fact]
    public async Task ItStillRestrictsOriginsWithPrivateNetworkAccessEnabledAsync()
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client)
        {
            AllowedOrigins = [new Uri("http://www.example.com")],
            AllowPrivateNetworkAccess = true
        };

        await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync("http://127.0.0.1/"));
        VerifyNoRequest(mockHandler);
    }

    [Fact]
    public async Task ItRejectsDisallowedOriginBeforeSendingAsync()
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri("http://www.example.com")] };

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync("http://notallowed.example.invalid/"));
        Assert.Equal("Sending requests to the provided location is not allowed.", exception.Message);
        VerifyNoRequest(mockHandler);
    }

    [Theory]
    [InlineData("GET")]
    [InlineData("POST")]
    [InlineData("PUT")]
    [InlineData("DELETE")]
    public async Task ItBlocksAllowedLocalhostUsingDefaultDnsResolverAsync(string method)
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedOrigins = [new Uri("http://localhost")] };

        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() => SendAsync(plugin, method, "http://localhost/"));

        Assert.Contains("loopback", exception.Message, StringComparison.Ordinal);
        VerifyNoRequest(mockHandler);
    }

    private static Task<string> SendAsync(HttpPlugin plugin, string method, string uri) =>
        method switch
        {
            "GET" => plugin.GetAsync(uri),
            "POST" => plugin.PostAsync(uri, "body"),
            "PUT" => plugin.PutAsync(uri, "body"),
            "DELETE" => plugin.DeleteAsync(uri),
            _ => throw new ArgumentOutOfRangeException(nameof(method))
        };

    private static void VerifyNoRequest(Mock<HttpMessageHandler> mockHandler) =>
        mockHandler.Protected().Verify(
            "SendAsync", Times.Never(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());

    private static async Task<(string? RequestLine, string? HostHeader)> ServeOneRequestAsync(
        TcpListener listener,
        CancellationToken cancellationToken,
        string responseBody = "")
    {
        using var connection = await listener.AcceptTcpClientAsync(cancellationToken);
        await using var stream = connection.GetStream();
        using var reader = new StreamReader(stream, Encoding.ASCII, leaveOpen: true);

        var requestLine = await reader.ReadLineAsync(cancellationToken);
        string? hostHeader = null;
        while (await reader.ReadLineAsync(cancellationToken) is { Length: > 0 } header)
        {
            if (header.StartsWith("Host:", StringComparison.OrdinalIgnoreCase))
            {
                hostHeader = header;
            }
        }

        var responseBytes = Encoding.ASCII.GetBytes(
            $"HTTP/1.1 200 OK\r\nContent-Length: {Encoding.ASCII.GetByteCount(responseBody)}\r\nConnection: close\r\n\r\n{responseBody}");
        await stream.WriteAsync(responseBytes, cancellationToken);
        return (requestLine, hostHeader);
    }

    private static async Task ObserveServerTaskAsync(Task? serverTask)
    {
        if (serverTask is null)
        {
            return;
        }

        try
        {
            await serverTask;
        }
        catch (OperationCanceledException)
        {
        }
        catch (SocketException)
        {
        }
        catch (ObjectDisposedException)
        {
        }
    }

    private Mock<HttpMessageHandler> CreateMock()
    {
        var mockHandler = new Mock<HttpMessageHandler>();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(this._response);
        return mockHandler;
    }

    private void VerifyMock(Mock<HttpMessageHandler> mockHandler, HttpMethod method)
    {
        mockHandler.Protected().Verify(
            "SendAsync",
            Times.Exactly(1), // we expected a single external request
            ItExpr.Is<HttpRequestMessage>(req =>
                    req.Method == method // we expected a POST request
                    && req.RequestUri == new Uri(this._uriString) // to this uri
            ),
            ItExpr.IsAny<CancellationToken>()
        );
    }

    public void Dispose()
    {
        this._response.Dispose();
    }
}
