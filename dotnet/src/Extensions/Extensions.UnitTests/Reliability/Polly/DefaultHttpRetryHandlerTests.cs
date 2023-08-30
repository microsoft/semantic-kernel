// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Reliability.Polly.Config;
using Moq;
using Moq.Protected;
using Polly.Timeout;
using Polly.Utilities;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Reliability.Polly;

public sealed class DefaultHttpRetryHandlerTests : IDisposable
{
    private Mock<DefaultHttpRetryHandler.ITimeProvider> _mockTimeProvider = new();

    public DefaultHttpRetryHandlerTests()
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
    public async Task NoMaxRetryCountCallsOnceForStatusAsync(HttpStatusCode statusCode)
    {
        // Arrange
        using var retry = new DefaultHttpRetryHandler(new HttpRetryConfig() { MaxRetryCount = 0 }, NullLoggerFactory.Instance);
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
    public async Task ItRetriesOnceOnRetryableStatusAsync(HttpStatusCode statusCode)
    {
        // Arrange
        using var retry = ConfigureRetryHandler();
        using var mockResponse = new HttpResponseMessage(statusCode);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
    }

    [Theory]
    [InlineData(typeof(HttpRequestException))]
    public async Task ItRetriesOnceOnRetryableExceptionAsync(Type exceptionType)
    {
        // Arrange
        using var retry = ConfigureRetryHandler();
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(exceptionType);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await Assert.ThrowsAsync(exceptionType,
            async () => await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Theory]
    [InlineData(typeof(HttpRequestException))]
    public async Task NoMaxRetryCountCallsOnceForExceptionAsync(Type exceptionType)
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { MaxRetryCount = 0 });
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(exceptionType);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await Assert.ThrowsAsync(exceptionType,
            async () => await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Theory]
    [InlineData(HttpStatusCode.RequestTimeout)]
    [InlineData(HttpStatusCode.ServiceUnavailable)]
    [InlineData(HttpStatusCode.GatewayTimeout)]
    [InlineData(HttpStatusCode.TooManyRequests)]
    public async Task ItRetriesOnceOnTransientStatusWithExponentialBackoffAsync(HttpStatusCode statusCode)
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { UseExponentialBackoff = true });
        using var mockResponse = new HttpResponseMessage(statusCode);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
    }

    [Theory]
    [InlineData(typeof(HttpRequestException))]
    public async Task ItRetriesOnceOnRetryableExceptionWithExponentialBackoffAsync(Type exceptionType)
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { UseExponentialBackoff = true });
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(exceptionType);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await Assert.ThrowsAsync(exceptionType,
            async () => await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Theory]
    [InlineData(HttpStatusCode.RequestTimeout)]
    [InlineData(HttpStatusCode.ServiceUnavailable)]
    [InlineData(HttpStatusCode.GatewayTimeout)]
    public async Task ItRetriesExponentiallyWithExponentialBackoffAsync(HttpStatusCode statusCode)
    {
        // Arrange
        var currentTime = DateTimeOffset.UtcNow;
        this._mockTimeProvider.SetupSequence(x => x.GetCurrentTime())
            .Returns(() => currentTime)
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(5))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(510))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(1015))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(1520));

        using var retry = ConfigureRetryHandler(new HttpRetryConfig()
        {
            UseExponentialBackoff = true, MaxRetryCount = 3,
            MinRetryDelay = TimeSpan.FromMilliseconds(500)
        }, this._mockTimeProvider);

        using var mockResponse = new HttpResponseMessage(statusCode);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(4), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
    }

    [Theory]
    [InlineData(HttpStatusCode.RequestTimeout)]
    [InlineData(HttpStatusCode.ServiceUnavailable)]
    [InlineData(HttpStatusCode.GatewayTimeout)]
    public async Task ItRetriesOnceOnTransientStatusCodeWithRetryValueAsync(HttpStatusCode statusCode)
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig(), null);
        using var mockResponse = new HttpResponseMessage()
        {
            StatusCode = statusCode,
            Headers = { RetryAfter = new RetryConditionHeaderValue(new TimeSpan(0, 0, 0, 1)) },
        };
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);
        using var testContent = new StringContent("test");

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
        Assert.Equal(new TimeSpan(0, 0, 0, 1), response.Headers.RetryAfter?.Delta);
    }

    [Theory]
    [InlineData(HttpStatusCode.RequestTimeout)]
    [InlineData(HttpStatusCode.ServiceUnavailable)]
    [InlineData(HttpStatusCode.GatewayTimeout)]
    public async Task ItRetriesStatusCustomCountAsync(HttpStatusCode expectedStatus)
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { MaxRetryCount = 3 }, null);
        using var mockResponse = new HttpResponseMessage(expectedStatus);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(4), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(expectedStatus, response.StatusCode);
    }

    [Theory]
    [InlineData(typeof(HttpRequestException))]
    public async Task ItRetriesExceptionsCustomCountAsync(Type expectedException)
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { MaxRetryCount = 3 }, null);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(expectedException);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await Assert.ThrowsAsync(expectedException,
            async () => await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(4), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Fact]
    public async Task NoExceptionNoRetryAsync()
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { MaxRetryCount = 3 }, null);
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.OK);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(1), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task ItDoesNotExecuteOnCancellationTokenAsync()
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { MaxRetryCount = 3 }, null);
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.OK);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);
        var cancellationToken = new CancellationToken(true);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await Assert.ThrowsAsync<TaskCanceledException>(async () =>
            await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, cancellationToken));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Never(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Fact]
    public async Task ItDoestExecuteOnFalseCancellationTokenAsync()
    {
        // Arrange
        using var retry = ConfigureRetryHandler(new HttpRetryConfig() { MaxRetryCount = 3 }, null);
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.OK);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);
        var cancellationToken = new CancellationToken(false);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, cancellationToken);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(1), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.OK, response.StatusCode);
    }

    [Fact]
    public async Task ItRetriesWithMinRetryDelayAsync()
    {
        var httpRetryConfig = new HttpRetryConfig
        {
            MinRetryDelay = TimeSpan.FromMilliseconds(500)
        };

        var mockTimeProvider = new Mock<DefaultHttpRetryHandler.ITimeProvider>();
        var (mockLoggerFactory, mockLogger) = GetLoggerMocks();
        using var retry = ConfigureRetryHandler(httpRetryConfig, mockTimeProvider, mockLoggerFactory);
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.TooManyRequests);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockLogger.Verify(l => l.Log(
            LogLevel.Warning,
            It.IsAny<EventId>(),
            It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("pausing 500ms")),
            It.IsAny<Exception>(),
            It.IsAny<Func<It.IsAnyType, Exception, string>>()!
            ), Times.AtLeastOnce);

        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.TooManyRequests, response.StatusCode);
    }

    [Fact]
    public async Task ItRetriesWithMaxRetryDelayAsync()
    {
        var httpRetryConfig = new HttpRetryConfig
        {
            MinRetryDelay = TimeSpan.FromMilliseconds(1),
            MaxRetryDelay = TimeSpan.FromMilliseconds(500)
        };

        var mockTimeProvider = new Mock<DefaultHttpRetryHandler.ITimeProvider>();
        var (mockLoggerFactory, mockLogger) = GetLoggerMocks();
        using var retry = ConfigureRetryHandler(httpRetryConfig, mockTimeProvider, mockLoggerFactory);
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.TooManyRequests)
        {
            Headers = { RetryAfter = new RetryConditionHeaderValue(TimeSpan.FromMilliseconds(2000)) }
        };
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockLogger.Verify(l => l.Log(
            LogLevel.Warning,
            It.IsAny<EventId>(),
            It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("pausing 500ms")),
            It.IsAny<Exception>(),
            It.IsAny<Func<It.IsAnyType, Exception, string>>()!
            ), Times.AtLeastOnce);

        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.TooManyRequests, response.StatusCode);
        Assert.Equal(TimeSpan.FromMilliseconds(2000), response.Headers.RetryAfter?.Delta);
    }

    [Theory]
    [InlineData(HttpStatusCode.TooManyRequests)]
    [InlineData(HttpStatusCode.ServiceUnavailable)]
    [InlineData(HttpStatusCode.GatewayTimeout)]
    [InlineData(HttpStatusCode.RequestTimeout)]
    public async Task ItRetriesWithMaxTotalDelayAsync(HttpStatusCode statusCode)
    {
        // Arrange
        var httpRetryConfig = new HttpRetryConfig
        {
            MaxRetryCount = 5,
            MinRetryDelay = TimeSpan.FromMilliseconds(50),
            MaxRetryDelay = TimeSpan.FromMilliseconds(50),
            MaxTotalRetryTime = TimeSpan.FromMilliseconds(350)
        };

        var mockTimeProvider = new Mock<DefaultHttpRetryHandler.ITimeProvider>();

        var currentTime = DateTimeOffset.UtcNow;
        mockTimeProvider.SetupSequence(x => x.GetCurrentTime())
            .Returns(() => currentTime)
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(5))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(55))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(110))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(165))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(220))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(275))
            .Returns(() => currentTime + TimeSpan.FromMilliseconds(330));

        using var retry = ConfigureRetryHandler(httpRetryConfig, mockTimeProvider);

        using var mockResponse = new HttpResponseMessage(statusCode);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(6), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(statusCode, response.StatusCode);
    }

    [Fact]
    public async Task ItRetriesFewerWithMaxTotalDelayAsync()
    {
        // Arrange
        var httpRetryConfig = new HttpRetryConfig
        {
            MaxRetryCount = 5,
            MinRetryDelay = TimeSpan.FromMilliseconds(50),
            MaxRetryDelay = TimeSpan.FromMilliseconds(50),
            MaxTotalRetryTime = TimeSpan.FromMilliseconds(100)
        };

        var mockTimeProvider = new Mock<DefaultHttpRetryHandler.ITimeProvider>();

        SystemClock.Reset();

        using var retry = ConfigureRetryHandler(httpRetryConfig, mockTimeProvider);

        using var mockResponse = new HttpResponseMessage(HttpStatusCode.TooManyRequests);
        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        await Assert.ThrowsAsync<TimeoutRejectedException>(
            () => httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Fact]
    public async Task ItRetriesFewerWithMaxTotalDelayOnExceptionAsync()
    {
        // Arrange
        var httpRetryConfig = new HttpRetryConfig
        {
            MaxRetryCount = 5,
            MinRetryDelay = TimeSpan.FromMilliseconds(50),
            MaxRetryDelay = TimeSpan.FromMilliseconds(50),
            MaxTotalRetryTime = TimeSpan.FromMilliseconds(100)
        };

        var mockTimeProvider = new Mock<DefaultHttpRetryHandler.ITimeProvider>();

        SystemClock.Reset();

        using var retry = ConfigureRetryHandler(httpRetryConfig, mockTimeProvider);
        var mockHandler = GetHttpMessageHandlerMock(typeof(HttpRequestException));

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        await Assert.ThrowsAsync<TimeoutRejectedException>(
            () => httpClient.GetAsync(new Uri("https://www.microsoft.com"), CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Fact]
    public async Task ItRetriesOnRetryableStatusCodesAsync()
    {
        // Arrange
        var config = new HttpRetryConfig() { RetryableStatusCodes = new List<HttpStatusCode> { HttpStatusCode.Unauthorized } };
        using var retry = ConfigureRetryHandler(config);
        using var mockResponse = new HttpResponseMessage(HttpStatusCode.Unauthorized);

        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(mockResponse);

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        var response = await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None);

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
        Assert.Equal(HttpStatusCode.Unauthorized, response.StatusCode);
    }

    [Fact]
    public async Task ItDoesNotRetryOnNonRetryableStatusCodesAsync()
    {
        // Arrange
        var config = new HttpRetryConfig() { RetryableStatusCodes = new List<HttpStatusCode> { HttpStatusCode.Unauthorized } };
        using var retry = ConfigureRetryHandler(config);
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
    public async Task ItRetriesOnRetryableExceptionsAsync()
    {
        // Arrange
        var config = new HttpRetryConfig() { RetryableExceptionTypes = new List<Type> { typeof(InvalidOperationException) } };
        using var retry = ConfigureRetryHandler(config);

        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(typeof(InvalidOperationException));

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Exactly(2), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    [Fact]
    public async Task ItDoesNotRetryOnNonRetryableExceptionsAsync()
    {
        // Arrange
        var config = new HttpRetryConfig() { RetryableExceptionTypes = new List<Type> { typeof(InvalidOperationException) } };
        using var retry = ConfigureRetryHandler(config);

        using var testContent = new StringContent("test");
        var mockHandler = GetHttpMessageHandlerMock(typeof(ArgumentException));

        retry.InnerHandler = mockHandler.Object;
        using var httpClient = new HttpClient(retry);

        // Act
        await Assert.ThrowsAsync<ArgumentException>(async () =>
            await httpClient.PostAsync(new Uri("https://www.microsoft.com"), testContent, CancellationToken.None));

        // Assert
        mockHandler.Protected()
            .Verify<Task<HttpResponseMessage>>("SendAsync", Times.Once(), ItExpr.IsAny<HttpRequestMessage>(), ItExpr.IsAny<CancellationToken>());
    }

    private static DefaultHttpRetryHandler ConfigureRetryHandler(HttpRetryConfig? config = null,
        Mock<DefaultHttpRetryHandler.ITimeProvider>? timeProvider = null, Mock<ILoggerFactory>? loggerFactoryMock = null)
    {
        timeProvider ??= new Mock<DefaultHttpRetryHandler.ITimeProvider>();

        var retry = new DefaultHttpRetryHandler(config ?? new HttpRetryConfig(), timeProvider.Object, loggerFactoryMock?.Object);
        return retry;
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
