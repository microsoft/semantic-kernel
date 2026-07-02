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
    private readonly string _uriString = "http://www.example.com";

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["www.example.com"] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["www.example.com"] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["www.example.com"] };

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
        var plugin = new HttpPlugin(client) { AllowedDomains = ["www.example.com"] };

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
        using var listener = new System.Net.HttpListener();
        var port = new Random().Next(49152, 65535);
        listener.Prefixes.Add($"http://localhost:{port}/");
        listener.Start();
        bool redirectTargetContacted = false;

        _ = Task.Run(async () =>
        {
            while (listener.IsListening)
            {
                try
                {
                    var ctx = await listener.GetContextAsync();
                    if (ctx.Request.Url!.AbsolutePath == "/start")
                    {
                        ctx.Response.StatusCode = 302;
                        ctx.Response.RedirectLocation = $"http://localhost:{port}/secret";
                        ctx.Response.Close();
                    }
                    else if (ctx.Request.Url.AbsolutePath == "/secret")
                    {
                        redirectTargetContacted = true;
                        ctx.Response.StatusCode = 200;
                        ctx.Response.Close();
                    }
                }
                catch (ObjectDisposedException) { break; }
                catch (System.Net.HttpListenerException) { break; }
            }
        });

        var plugin = new HttpPlugin()
        {
            AllowedDomains = ["localhost"]
        };

        // Act & Assert - the plugin should throw because 302 is a non-success status
        await Assert.ThrowsAsync<HttpOperationException>(() => plugin.GetAsync($"http://localhost:{port}/start"));
        Assert.False(redirectTargetContacted, "The redirect target should not have been contacted.");

        listener.Stop();
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
