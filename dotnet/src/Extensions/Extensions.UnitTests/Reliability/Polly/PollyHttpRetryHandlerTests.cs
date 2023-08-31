// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Net;
using System.Net.Http;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Reliability.Polly;
using Moq;
using Moq.Protected;
using Polly;
using Polly.Utilities;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Reliability.Polly;

public sealed class PollyHttpRetryHandlerTests : IDisposable
{
    public PollyHttpRetryHandlerTests()
    {
        SystemClock.SleepAsync = (_, _) => Task.CompletedTask;
        SystemClock.Sleep = (_, _) => { };
    }

    public void Dispose()
    {
        SystemClock.Reset();
    }

    [Theory]
    [InlineData(HttpStatusCode.RequestTimeout)]
    [InlineData(HttpStatusCode.ServiceUnavailable)]
    [InlineData(HttpStatusCode.GatewayTimeout)]
    [InlineData(HttpStatusCode.TooManyRequests)]
    public async Task CustomPolicyNoOpShouldNotAvoidSendRequests(HttpStatusCode statusCode)
    {
        // Arrange
        var asyncPolicy = Policy.NoOpAsync<HttpResponseMessage>();
        var (mockLoggerFactory, mockLogger) = GetLoggerMocks();
        using var retry = new PollyHttpRetryHandler(asyncPolicy, mockLoggerFactory.Object);
        using var mockResponse = new HttpResponseMessage(statusCode);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
    }

    [Theory]
    [InlineData(HttpStatusCode.RequestTimeout)]
    [InlineData(HttpStatusCode.ServiceUnavailable)]
    [InlineData(HttpStatusCode.GatewayTimeout)]
    [InlineData(HttpStatusCode.TooManyRequests)]
    public async Task CustomPolicyStatusDontMatchNeverTriggers(HttpStatusCode statusCode)
    {
        // Arrange
        var asyncPolicy = Policy
            .HandleResult<HttpResponseMessage>(result => result.StatusCode != statusCode)
            .WaitAndRetryAsync<HttpResponseMessage>(
                retryCount: 1,
                sleepDurationProvider: (retryTimes) => TimeSpan.FromMilliseconds(10));

        var (mockLoggerFactory, mockLogger) = GetLoggerMocks();
        using var retry = new PollyHttpRetryHandler(asyncPolicy, mockLoggerFactory.Object);
        using var mockResponse = new HttpResponseMessage(statusCode);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
    }

    [Theory]
    [InlineData(HttpStatusCode.RequestTimeout, HttpStatusCode.TooManyRequests)]
    [InlineData(HttpStatusCode.ServiceUnavailable, HttpStatusCode.TooManyRequests)]
    [InlineData(HttpStatusCode.GatewayTimeout, HttpStatusCode.TooManyRequests)]
    [InlineData(HttpStatusCode.TooManyRequests, HttpStatusCode.TooManyRequests)]
    public async Task CustomPolicyRetryStatusShouldTriggerRetrials(HttpStatusCode statusCode, HttpStatusCode retryStatusCode)
    {
        // Arrange
        var retryCount = 3;
        var asyncPolicy = Policy
            .HandleResult<HttpResponseMessage>(result => result.StatusCode == retryStatusCode)
            .WaitAndRetryAsync<HttpResponseMessage>(
                retryCount,
                (retryNumber) => TimeSpan.FromMilliseconds(10));

        var (mockLoggerFactory, mockLogger) = GetLoggerMocks();
        using var retry = new PollyHttpRetryHandler(asyncPolicy, mockLoggerFactory.Object);
        using var mockResponse = new HttpResponseMessage(statusCode);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        var expectedSendAsyncTimes = (statusCode == retryStatusCode)
            ? retryCount + 1
            : 1;

        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(expectedSendAsyncTimes), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
    }

    [Theory]
    [InlineData(typeof(ApplicationException), typeof(HttpRequestException))]
    [InlineData(typeof(HttpRequestException), typeof(HttpRequestException))]
    public async Task CustomPolicyRetryExceptionsShouldTriggerRetrials(Type exceptionType, Type retryExceptionType)
    {
        // Arrange
        var retryCount = 1;
        var asyncPolicy = Policy.Handle<Exception>(exception => exception.GetType() == retryExceptionType)
            .WaitAndRetryAsync(
                retryCount,
                (retryNumber) => TimeSpan.FromMilliseconds(10));

        var (mockLoggerFactory, mockLogger) = GetLoggerMocks();
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(exceptionType);
        using var retry = new PollyHttpRetryHandler(asyncPolicy, mockLoggerFactory.Object);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await Assert.ThrowsAsync(exceptionType,
            async () => await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        var expectedSendAsyncTimes = (exceptionType == retryExceptionType)
            ? retryCount + 1
            : 1;

        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(expectedSendAsyncTimes), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    private static (Mock<ILoggerFactory>, Mock<ILogger>) GetLoggerMocks()
    {
        var mockLoggerFactory = new Mock<ILoggerFactory>();
        var mockLogger = new Mock<ILogger>();
        mockLoggerFactory.Setup(x => x.CreateLogger(It.IsAny<string>())).Returns(mockLogger.Object);

        return (mockLoggerFactory, mockLogger);
    }

    private static Mock<HttpMessageHandler> GetHttpMessageHandlerMock(HttpResponseMessage mockResponse)
    {
        var mockHandler = new Mock<HttpMessageHandler>();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ReturnsAsync(mockResponse);
        return mockHandler;
    }

    private static Mock<HttpMessageHandler> GetHttpMessageHandlerMock(Type exceptionType)
    {
        var mockHandler = new Mock<HttpMessageHandler>();
        mockHandler.Protected()
            .Setup<Task<HttpResponseMessage>>("SendAsync", ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>())
            .ThrowsAsync(Activator.CreateInstance(exceptionType) as Exception);
        return mockHandler;
    }
}
