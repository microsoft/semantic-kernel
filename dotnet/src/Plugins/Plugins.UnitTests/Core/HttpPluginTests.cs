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

public class HttpPluginTests : IDisposable
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
        // Arrange
        var kernel = KernelBuilder.Create();
        var plugin = new HttpPlugin();

        // Act - Assert no exception occurs e.g. due to reflection
        kernel.ImportFunctions(plugin, "http");
    }

    [Fact]
    public async Task ItCanGetAsync()
    {
        // Arrange
        var mockHandler = this.CreateMock();
        using var client = new HttpClient(mockHandler.Object);
        var plugin = new HttpPlugin(client);

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
        var plugin = new HttpPlugin(client);

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
        var plugin = new HttpPlugin(client);

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
        var plugin = new HttpPlugin(client);

        // Act
        var result = await plugin.DeleteAsync(this._uriString);

        // Assert
        Assert.Equal(this._content, result);
        this.VerifyMock(mockHandler, HttpMethod.Delete);
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
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._response.Dispose();
        }
    }
}
