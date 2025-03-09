// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingVectorStoreBuilderExtensionsTests
{
    [Fact]
    public void UseLoggingWithFactoryAddsDecorator()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory.Setup(f => f.CreateLogger(It.IsAny<string>())).Returns(new Mock<ILogger>().Object);
        var builder = new VectorStoreBuilder(innerStore);

        // Act
        builder.UseLogging(loggerFactory.Object);
        var result = builder.Build();

        // Assert
        Assert.IsType<LoggingVectorStore>(result);
    }

    [Fact]
    public void UseLoggingWithNullFactoryResolvesFromServiceProvider()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory.Setup(f => f.CreateLogger(It.IsAny<string>())).Returns(new Mock<ILogger>().Object);
        var serviceProvider = new Mock<IServiceProvider>();
        serviceProvider.Setup(sp => sp.GetService(typeof(ILoggerFactory))).Returns(loggerFactory.Object);
        var builder = new VectorStoreBuilder(innerStore);

        // Act
        builder.UseLogging();
        var result = builder.Build(serviceProvider.Object);

        // Assert
        Assert.IsType<LoggingVectorStore>(result);
    }

    [Fact]
    public void UseLoggingWithNullLoggerFactoryReturnsInnerStore()
    {
        // Arrange
        var innerStore = new Mock<IVectorStore>().Object;
        var builder = new VectorStoreBuilder(innerStore);

        // Act
        builder.UseLogging(NullLoggerFactory.Instance);
        var result = builder.Build();

        // Assert
        Assert.Same(innerStore, result);
    }
}
