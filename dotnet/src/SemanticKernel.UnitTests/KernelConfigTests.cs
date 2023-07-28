// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Reliability;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests;

/// <summary>
/// Unit tests of <see cref="KernelConfig"/>.
/// </summary>
public class KernelConfigTests
{
    private readonly Mock<IKernel> _kernel;

    public KernelConfigTests()
    {
        var kernelConfig = new KernelConfig();
        this._kernel = new Mock<IKernel>();
        this._kernel.SetupGet(x => x.Logger).Returns(NullLogger.Instance);
        this._kernel.SetupGet(x => x.Config).Returns(kernelConfig);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSet()
    {
        // Arrange
        var retry = new NullHttpRetryHandlerFactory();
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(retry);

        // Assert
        Assert.Equal(retry, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetWithCustomImplementation()
    {
        // Arrange
        var retry = new Mock<IDelegatingHandlerFactory>();
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(retry.Object);

        // Assert
        Assert.Equal(retry.Object, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetToDefaultHttpRetryHandlerFactoryIfNull()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        config.SetHttpRetryHandlerFactory(null);

        // Assert
        Assert.IsType<DefaultHttpRetryHandlerFactory>(config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpRetryHandlerFactoryIsSetToDefaultHttpRetryHandlerFactoryIfNotSet()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        // Assert
        Assert.IsType<DefaultHttpRetryHandlerFactory>(config.HttpHandlerFactory);
    }
}
