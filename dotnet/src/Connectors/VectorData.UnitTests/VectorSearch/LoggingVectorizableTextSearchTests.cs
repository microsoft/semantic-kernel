// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingVectorizableTextSearchTests : BaseLoggingTests
{
    [Fact]
    public void ConstructorThrowsOnNullInnerSearch()
    {
        // Arrange
        var logger = new Mock<ILogger>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorizableTextSearch<string>(null!, logger));
    }

    [Fact]
    public void ConstructorThrowsOnNullLogger()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizableTextSearch<string>>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingVectorizableTextSearch<string>(innerSearch, null!));
    }

    [Fact]
    public async Task VectorizableTextSearchDelegatesToInnerSearchAsync()
    {
        // Arrange
        var innerSearch = new Mock<IVectorizableTextSearch<string>>();
        var logger = new FakeLogger();
        var searchText = "test";
        var options = new VectorSearchOptions<string>();
        var searchResults = new[] { new VectorSearchResult<string>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<string>(searchResults);
        innerSearch.Setup(s => s.VectorizableTextSearchAsync(searchText, options, default))
                   .ReturnsAsync(results);
        var decorator = new LoggingVectorizableTextSearch<string>(innerSearch.Object, logger);

        // Act
        var actualResults = await decorator.VectorizableTextSearchAsync(searchText, options);

        // Assert
        Assert.Same(results, actualResults);
        innerSearch.Verify(s => s.VectorizableTextSearchAsync(searchText, options, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "VectorizableTextSearchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "VectorizableTextSearchAsync completed.");
    }
}
