// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Moq;
using Xunit;

namespace VectorData.UnitTests;

public class LoggingKeywordHybridSearchTests : BaseLoggingTests
{
    [Fact]
    public void ConstructorThrowsOnNullInnerSearch()
    {
        // Arrange
        var logger = new Mock<ILogger>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingKeywordHybridSearch<string>(null!, logger));
    }

    [Fact]
    public void ConstructorThrowsOnNullLogger()
    {
        // Arrange
        var innerSearch = new Mock<IKeywordHybridSearch<string>>().Object;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new LoggingKeywordHybridSearch<string>(innerSearch, null!));
    }

    [Fact]
    public async Task HybridSearchDelegatesToInnerSearchAsync()
    {
        // Arrange
        var innerSearch = new Mock<IKeywordHybridSearch<string>>();
        var logger = new FakeLogger();
        var vector = new float[] { 1.0f };
        var keywords = new List<string> { "test" };
        var options = new HybridSearchOptions<string>();
        var searchResults = new[] { new VectorSearchResult<string>("result", 0.9f) }.ToAsyncEnumerable();
        var results = new VectorSearchResults<string>(searchResults);

        innerSearch.Setup(s => s.HybridSearchAsync(vector, keywords, options, default))
                   .ReturnsAsync(results);

        var decorator = new LoggingKeywordHybridSearch<string>(innerSearch.Object, logger);

        // Act
        var actualResults = await decorator.HybridSearchAsync(vector, keywords, options);

        // Assert
        Assert.Same(results, actualResults);
        innerSearch.Verify(s => s.HybridSearchAsync(vector, keywords, options, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "HybridSearchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "HybridSearchAsync completed.");
    }

    [Fact]
    public async Task HybridSearchLogsCancellationAsync()
    {
        // Arrange
        var logger = new FakeLogger();

        var vector = new float[] { 1.0f };
        var keywords = new List<string> { "test" };
        var options = new HybridSearchOptions<string>();

        using var cts = new CancellationTokenSource();
        cts.Cancel();

        var innerSearch = new Mock<IKeywordHybridSearch<string>>();
        innerSearch.Setup(s => s.HybridSearchAsync(vector, keywords, options, cts.Token))
                   .Returns(Task.FromCanceled<VectorSearchResults<string>>(cts.Token));

        var decorator = new LoggingKeywordHybridSearch<string>(innerSearch.Object, logger);

        // Act & Assert
        await Assert.ThrowsAsync<TaskCanceledException>(() =>
            decorator.HybridSearchAsync(vector, keywords, options, cts.Token));

        innerSearch.Verify(s => s.HybridSearchAsync(vector, keywords, options, cts.Token), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "HybridSearchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Debug, "HybridSearchAsync canceled.");
    }

    [Fact]
    public async Task HybridSearchLogsExceptionAsync()
    {
        // Arrange
        var logger = new FakeLogger();

        var vector = new float[] { 1.0f };
        var keywords = new List<string> { "test" };
        var options = new HybridSearchOptions<string>();

        var innerSearch = new Mock<IKeywordHybridSearch<string>>();
        innerSearch.Setup(s => s.HybridSearchAsync(vector, keywords, options, default))
                   .ThrowsAsync(new InvalidOperationException("Test exception"));

        var decorator = new LoggingKeywordHybridSearch<string>(innerSearch.Object, logger);

        // Act & Assert
        var exception = await Assert.ThrowsAsync<InvalidOperationException>(() =>
            decorator.HybridSearchAsync(vector, keywords, options, default));

        innerSearch.Verify(s => s.HybridSearchAsync(vector, keywords, options, default), Times.Once());

        AssertLog(logger.Logs, LogLevel.Debug, "HybridSearchAsync invoked.");
        AssertLog(logger.Logs, LogLevel.Error, "HybridSearchAsync failed.", exception);

        Assert.Equal("Test exception", logger.Logs[1].Exception?.Message);
    }
}
