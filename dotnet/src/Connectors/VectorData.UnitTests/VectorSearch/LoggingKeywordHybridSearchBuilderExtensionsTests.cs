// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingKeywordHybridSearchBuilderExtensionsTests
{
    [Fact]
    public void UseLoggingWithFactoryAddsDecorator()
    {
        // Arrange
        var innerSearch = new Mock<IKeywordHybridSearch<string>>().Object;
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory.Setup(f => f.CreateLogger(It.IsAny<string>())).Returns(new Mock<ILogger>().Object);
        var builder = new KeywordHybridSearchBuilder<string>(innerSearch);

        // Act
        builder.UseLogging(loggerFactory.Object);
        var result = builder.Build();

        // Assert
        Assert.IsType<LoggingKeywordHybridSearch<string>>(result);
    }

    [Fact]
    public void UseLoggingWithNullFactoryResolvesFromServiceProvider()
    {
        // Arrange
        var innerSearch = new Mock<IKeywordHybridSearch<string>>().Object;
        var loggerFactory = new Mock<ILoggerFactory>();
        loggerFactory.Setup(f => f.CreateLogger(It.IsAny<string>())).Returns(new Mock<ILogger>().Object);
        var serviceProvider = new Mock<IServiceProvider>();
        serviceProvider.Setup(sp => sp.GetService(typeof(ILoggerFactory))).Returns(loggerFactory.Object);
        var builder = new KeywordHybridSearchBuilder<string>(innerSearch);

        // Act
        builder.UseLogging();
        var result = builder.Build(serviceProvider.Object);

        // Assert
        Assert.IsType<LoggingKeywordHybridSearch<string>>(result);
    }

    [Fact]
    public void UseLoggingWithNullLoggerFactoryReturnsInnerSearch()
    {
        // Arrange
        var innerSearch = new Mock<IKeywordHybridSearch<string>>().Object;
        var builder = new KeywordHybridSearchBuilder<string>(innerSearch);

        // Act
        builder.UseLogging(NullLoggerFactory.Instance);
        var result = builder.Build();

        // Assert
        Assert.Same(innerSearch, result);
    }
}
