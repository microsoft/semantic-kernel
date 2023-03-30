// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Reliability;
using Xunit;

namespace SemanticKernel.UnitTests.Reliability;

/// <summary>
/// Unit tests of <see cref="KernelConfig"/>.
/// </summary>
public class HttpRetryConfigTests
{
    [Fact]
    public async Task NegativeMaxRetryCountThrowsAsync()
    {
        // Act
        await Assert.ThrowsAsync<System.ArgumentOutOfRangeException>(() =>
        {
            var httpRetryConfig = new HttpRetryConfig() { MaxRetryCount = -1 };
            return Task.CompletedTask;
        });
    }

    [Fact]
    public void SetDefaultHttpRetryConfig()
    {
        // Arrange
        var config = new KernelConfig();
        var httpRetryConfig = new HttpRetryConfig() { MaxRetryCount = 1 };

        // Act
        config.SetDefaultHttpRetryConfig(httpRetryConfig);

        // Assert
        Assert.Equal(httpRetryConfig, config.DefaultHttpRetryConfig);
    }

    [Fact]
    public void SetDefaultHttpRetryConfigToDefaultIfNotSet()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        // Assert
        var defaultConfig = new HttpRetryConfig();
        Assert.Equal(defaultConfig.MaxRetryCount, config.DefaultHttpRetryConfig.MaxRetryCount);
        Assert.Equal(defaultConfig.MaxRetryDelay, config.DefaultHttpRetryConfig.MaxRetryDelay);
        Assert.Equal(defaultConfig.MinRetryDelay, config.DefaultHttpRetryConfig.MinRetryDelay);
        Assert.Equal(defaultConfig.MaxTotalRetryTime, config.DefaultHttpRetryConfig.MaxTotalRetryTime);
        Assert.Equal(defaultConfig.UseExponentialBackoff, config.DefaultHttpRetryConfig.UseExponentialBackoff);
        Assert.Equal(defaultConfig.RetryableStatusCodes, config.DefaultHttpRetryConfig.RetryableStatusCodes);
        Assert.Equal(defaultConfig.RetryableExceptionTypes, config.DefaultHttpRetryConfig.RetryableExceptionTypes);
    }

    [Fact]
    public void SetDefaultHttpRetryConfigToDefaultIfNull()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        config.SetDefaultHttpRetryConfig(null);

        // Assert
        var defaultConfig = new HttpRetryConfig();
        Assert.Equal(defaultConfig.MaxRetryCount, config.DefaultHttpRetryConfig.MaxRetryCount);
        Assert.Equal(defaultConfig.MaxRetryDelay, config.DefaultHttpRetryConfig.MaxRetryDelay);
        Assert.Equal(defaultConfig.MinRetryDelay, config.DefaultHttpRetryConfig.MinRetryDelay);
        Assert.Equal(defaultConfig.MaxTotalRetryTime, config.DefaultHttpRetryConfig.MaxTotalRetryTime);
        Assert.Equal(defaultConfig.UseExponentialBackoff, config.DefaultHttpRetryConfig.UseExponentialBackoff);
        Assert.Equal(defaultConfig.RetryableStatusCodes, config.DefaultHttpRetryConfig.RetryableStatusCodes);
        Assert.Equal(defaultConfig.RetryableExceptionTypes, config.DefaultHttpRetryConfig.RetryableExceptionTypes);
    }
}
