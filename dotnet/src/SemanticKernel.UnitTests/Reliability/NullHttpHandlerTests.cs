// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Moq;
using Moq.Protected;
using Xunit;

namespace SemanticKernel.UnitTests.Reliability;

public class NullHttpHandlerTests
{
    [Fact]
    public async Task ItDoesNotRetryOnExceptionAsync()
    {
        // Arrange
        using var retry = new NullHttpHandler();
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.TooManyRequests);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);
        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.TooManyRequests, response.StatusCode);
    }

    [Fact]
    public async Task NoExceptionNoRetryAsync()
    {
        // Arrange
        using var retry = new NullHttpHandler();
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.OK);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);
        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task TaskCanceledExceptionThrownOnCancellationTokenAsync()
    {
        // Arrange
        using var retry = new NullHttpHandler();
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.TooManyRequests);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);
        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);
        using var cancellationTokenSource = new CancellationTokenSource();
        cancellationTokenSource.Cancel();

        // Act
        await Assert.ThrowsAsync<TaskCanceledException>(async () =>
            await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, cancellationTokenSource.Token));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Fact]
    public async Task ItDoestExecuteOnFalseCancellationTokenAsync()
    {
        // Arrange
        using var retry = new NullHttpHandler();
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.TooManyRequests);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);
        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, new CancellationToken(false));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.TooManyRequests, response.StatusCode);
    }

    private static Mock<HttpMessageHandler> GetHttpMessageHandlerMock(HttpResponseMessage mockResponse)
    {
        var mockHandler = new Mock<HttpMessageHandler>();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(mockResponse);
        return mockHandler;
    }
}
