// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Plugins.Core;
using Moq;
using Moq.Protected;
using Xunit;

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["1.1.1.1"] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["1.1.1.1"] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["1.1.1.1"] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["1.1.1.1"] };

        // Act
        var result = await plugin.DeleteAsync(this._uriString);

        // Assert
        Assert.Equal(this._content, result);
        this.VerifyMock(mockHandler, HttpMethod.Delete);
    }

    [Fact]
    public async Task ItDeniesAllDomainsWithDefaultConfigAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client);

        // Act & Assert - default config denies all domains
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.GetAsync(this._uriString));
    }

    [Fact]
    public async Task ItThrowsInvalidOperationExceptionForInvalidDomainAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client)
        {
            AllowedDomains = ["www.example.com"]
        };
        var invalidUri = "http://www.notexample.com";

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.GetAsync(invalidUri));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.PostAsync(invalidUri, this._content));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.PutAsync(invalidUri, this._content));
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await plugin.DeleteAsync(invalidUri));
    }

    [Fact]
    public async Task ItDoesNotFollowRedirectsAsync()
    {
        // Arrange - start a local server that always returns a 302 redirect
        await using var server = new RedirectLoopbackServer("secret", "text/plain", []);

        var plugin = new HttpPlugin()
        {
            AllowedDomains = [server.BaseUri.Host],
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
            var plugin = new HttpPlugin(client) { AllowedDomains = [uri.Host] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = [uri.Host] };

        Assert.Equal(this._content, await plugin.GetAsync(uri.AbsoluteUri));
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
            AllowedDomains = [host],
            AllowPrivateNetworkAccess = true
        };

        Assert.Equal(this._content, await SendAsync(plugin, method, $"http://{host}/"));
    }

    [Fact]
    public async Task ItStillRestrictsDomainsWithPrivateNetworkAccessEnabledAsync()
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client)
        {
            AllowedDomains = ["www.example.com"],
            AllowPrivateNetworkAccess = true
        };

        await Assert.ThrowsAsync<InvalidOperationException>(() => plugin.GetAsync("http://127.0.0.1/"));
        VerifyNoRequest(mockHandler);
    }

    [Fact]
    public async Task ItRejectsDisallowedDomainBeforeSendingAsync()
    {
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client) { AllowedDomains = ["www.example.com"] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["localhost"] };

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
