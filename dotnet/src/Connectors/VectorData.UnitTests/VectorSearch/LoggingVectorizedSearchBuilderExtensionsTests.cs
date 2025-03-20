// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingVectorizedSearchBuilderExtensionsTests
{
    [Fact]
    public void UseLoggingWithFactoryAddsDecorator()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizedSearch<string>>().Object;
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory.Setup(f => f.CreateLogger(It.IsAny<string>())).Returns(new Mock<ILogger>().Object);
        var builder = new VectorizedSearchBuilder<string>(innerSearch);

        // Act
        builder.UseLogging(loggerFactory.Object);
        var result = builder.Build();

        // Assert
        Assert.IsType<LoggingVectorizedSearch<string>>(result);
    }

    [Fact]
    public void UseLoggingWithNullFactoryResolvesFromServiceProvider()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizedSearch<string>>().Object;
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory.Setup(f => f.CreateLogger(It.IsAny<string>())).Returns(new Mock<ILogger>().Object);
        var serviceProvider = new Mock<IServiceProvider>();
        serviceProvider.Setup(sp => sp.GetService(typeof(ILoggerFactory))).Returns(loggerFactory.Object);
        var builder = new VectorizedSearchBuilder<string>(innerSearch);

        // Act
        builder.UseLogging();
        var result = builder.Build(serviceProvider.Object);

        // Assert
        Assert.IsType<LoggingVectorizedSearch<string>>(result);
    }

    [Fact]
    public void UseLoggingWithNullLoggerFactoryReturnsInnerSearch()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizedSearch<string>>().Object;
        var builder = new VectorizedSearchBuilder<string>(innerSearch);

        // Act
        builder.UseLogging(NullLoggerFactory.Instance);
        var result = builder.Build();

        // Assert
        Assert.Same(innerSearch, result);
    }
}
