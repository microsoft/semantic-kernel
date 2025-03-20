// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingVectorizedSearchTests : BaseLoggingTests
{
    [Fact]
    public void ConstructorThrowsOnNullInnerSearch()
    {
        // Arrange
        var logger = new Mock<ILogger>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorizedSearch<string>(null!, logger));
    }

    [Fact]
    public void ConstructorThrowsOnNullLogger()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizedSearch<string>>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorizedSearch<string>(innerSearch, null!));
    }

    [Fact]
    public async Task VectorizedSearchDelegatesToInnerSearchAsync()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizedSearch<string>>();
        var logger = new FakeLogger();
        var vector = new float[] { 1.0f };
        var options = new VectorSearchOptions<string>();
        var searchResults = new[] { new VectorSearchResult<string>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<string>(searchResults);
        innerSearch.Setup(s => s.VectorizedSearchAsync(vector, options, default))
                   .ReturnsAsync(results);
        var decorator = new LoggingVectorizedSearch<string>(innerSearch.Object, logger);

        // Act
        var actualResults = await decorator.VectorizedSearchAsync(vector, options);

        // Assert
        Assert.Same(results, actualResults);
        innerSearch.Verify(s => s.VectorizedSearchAsync(vector, options, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizedSearchAsync completed.");
    }
}
