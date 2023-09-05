// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Reliability.Basic;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Reliability.Basic;

/// <summary>
/// Unit tests of <see cref="BasicRetryConfig"/>.
/// </summary>
public class BasicRetryConfigTests
{
    [Fact]
    public async Task NegativeMaxRetryCountThrowsAsync()
    {
        // Act
        await Assert.ThrowsAsync<System.ArgumentOutOfRangeException>(() =>
        {
            var BasicRetryConfig = new BasicRetryConfig() { MaxRetryCount = -1 };
            return Task.CompletedTask;
        });
    }

    [Fact]
    public void SetDefaultBasicRetryConfig()
    {
        // Arrange
        var builder = new KernelBuilder();
        var basicRetryConfig = new BasicRetryConfig() { MaxRetryCount = 1 };

        // Act
        builder.WithRetryBasic(basicRetryConfig);

        // Assert
        Assert.IsType<BasicHttpRetryHandlerFactory>(builder.HttpHandlerFactory);
        var httpHandlerFactory = builder.HttpHandlerFactory as BasicHttpRetryHandlerFactory;
        Assert.NotNull(httpHandlerFactory);
        Assert.Equal(basicRetryConfig, httpHandlerFactory.Config);
    }

    [Fact]
    public void SetDefaultBasicRetryConfigToDefaultIfNotSet()
    {
        // Arrange
        var retryConfig = new BasicRetryConfig();
        var builder = new KernelBuilder();

        // Act
        builder.WithRetryBasic(retryConfig);

        // Assert
        Assert.IsType<BasicHttpRetryHandlerFactory>(builder.HttpHandlerFactory);
        var httpHandlerFactory = builder.HttpHandlerFactory as BasicHttpRetryHandlerFactory;
        Assert.NotNull(httpHandlerFactory);
        Assert.Equal(retryConfig.MaxRetryCount, httpHandlerFactory.Config.MaxRetryCount);
        Assert.Equal(retryConfig.MaxRetryDelay, httpHandlerFactory.Config.MaxRetryDelay);
        Assert.Equal(retryConfig.MinRetryDelay, httpHandlerFactory.Config.MinRetryDelay);
        Assert.Equal(retryConfig.MaxTotalRetryTime, httpHandlerFactory.Config.MaxTotalRetryTime);
        Assert.Equal(retryConfig.UseExponentialBackoff, httpHandlerFactory.Config.UseExponentialBackoff);
        Assert.Equal(retryConfig.RetryableStatusCodes, httpHandlerFactory.Config.RetryableStatusCodes);
        Assert.Equal(retryConfig.RetryableExceptionTypes, httpHandlerFactory.Config.RetryableExceptionTypes);
    }
}
