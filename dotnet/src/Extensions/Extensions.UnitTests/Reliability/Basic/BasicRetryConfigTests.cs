// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Reliability.Basic;
using Xunit;

namespace SemanticKernel.Extensions.UnitTests.Reliability.Basic;

/// <summary>
/// Unit tests of <see cref="KernelConfig"/>.
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
        var config = new KernelConfig();
        var basicRetryConfig = new BasicRetryConfig() { MaxRetryCount = 1 };

        // Act
        config.SetRetryBasic(basicRetryConfig);

        // Assert
        Assert.IsType<BasicHttpRetryHandlerFactory>(config.HttpHandlerFactory);
        var httpHandlerFactory = config.HttpHandlerFactory as BasicHttpRetryHandlerFactory;
        Assert.NotNull(httpHandlerFactory);
        Assert.Equal(basicRetryConfig, httpHandlerFactory.Config);
    }

    [Fact]
    public void SetDefaultBasicRetryConfigToDefaultIfNotSet()
    {
        // Arrange
        var config = new KernelConfig();
        var retryConfig = new BasicRetryConfig();

        // Act
        config.SetRetryBasic(retryConfig);

        // Assert
        Assert.IsType<BasicHttpRetryHandlerFactory>(config.HttpHandlerFactory);
        var httpHandlerFactory = config.HttpHandlerFactory as BasicHttpRetryHandlerFactory;
        Assert.NotNull(httpHandlerFactory);
        Assert.Equal(retryConfig.MaxRetryCount, httpHandlerFactory.Config.MaxRetryCount);
        Assert.Equal(retryConfig.MaxRetryDelay, httpHandlerFactory.Config.MaxRetryDelay);
        Assert.Equal(retryConfig.MinRetryDelay, httpHandlerFactory.Config.MinRetryDelay);
        Assert.Equal(retryConfig.MaxTotalRetryTime, httpHandlerFactory.Config.MaxTotalRetryTime);
        Assert.Equal(retryConfig.UseExponentialBackoff, httpHandlerFactory.Config.UseExponentialBackoff);
        Assert.Equal(retryConfig.RetryableStatusCodes, httpHandlerFactory.Config.RetryableStatusCodes);
        Assert.Equal(retryConfig.RetryableExceptionTypes, httpHandlerFactory.Config.RetryableExceptionTypes);
    }

    [Fact]
    public void SetDefaultBasicRetryConfigToDefaultIfNull()
    {
        // Arrange
        var config = new KernelConfig();
        var defaultConfig = new BasicRetryConfig();

        // Act
        config.SetRetryBasic();

        // Assert
        Assert.IsType<BasicHttpRetryHandlerFactory>(config.HttpHandlerFactory);
        var httpHandlerFactory = config.HttpHandlerFactory as BasicHttpRetryHandlerFactory;

        Assert.NotNull(httpHandlerFactory);
        Assert.Equal(defaultConfig.MaxRetryCount, httpHandlerFactory.Config.MaxRetryCount);
        Assert.Equal(defaultConfig.MaxRetryDelay, httpHandlerFactory.Config.MaxRetryDelay);
        Assert.Equal(defaultConfig.MinRetryDelay, httpHandlerFactory.Config.MinRetryDelay);
        Assert.Equal(defaultConfig.MaxTotalRetryTime, httpHandlerFactory.Config.MaxTotalRetryTime);
        Assert.Equal(defaultConfig.UseExponentialBackoff, httpHandlerFactory.Config.UseExponentialBackoff);
        Assert.Equal(defaultConfig.RetryableStatusCodes, httpHandlerFactory.Config.RetryableStatusCodes);
        Assert.Equal(defaultConfig.RetryableExceptionTypes, httpHandlerFactory.Config.RetryableExceptionTypes);
    }
}
