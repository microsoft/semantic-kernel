// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel;
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
    public void HttpHandlerFactoryIsSet()
    {
        // Arrange
        var retry = new NullHttpHandlerFactory();
        var config = new KernelConfig();

        // Act
        config.SetHttpHandlerFactory(retry);

        // Assert
        Assert.Equal(retry, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpHandlerFactoryIsSetWithCustomImplementation()
    {
        // Arrange
        var retry = new Mock<IDelegatingHandlerFactory>();
        var config = new KernelConfig();

        // Act
        config.SetHttpHandlerFactory(retry.Object);

        // Assert
        Assert.Equal(retry.Object, config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpHandlerFactoryIsSetToNullHttpHandlerFactoryIfNull()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        config.SetHttpHandlerFactory(null);

        // Assert
        Assert.IsType<NullHttpHandlerFactory>(config.HttpHandlerFactory);
    }

    [Fact]
    public void HttpHandlerFactoryIsSetToNullHttpHandlerFactoryIfNotSet()
    {
        // Arrange
        var config = new KernelConfig();

        // Act
        // Assert
        Assert.IsType<NullHttpHandlerFactory>(config.HttpHandlerFactory);
    }
}
