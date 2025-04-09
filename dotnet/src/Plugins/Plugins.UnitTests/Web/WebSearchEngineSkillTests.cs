// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.Web;
using Moq;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.Web;

public sealed class WebSearchEnginePluginTests
{
    [Fact]
    public async Task SearchAsyncSucceedsAsync()
    {
        // Arrange
        IEnumerable<string> expected = [Guid.NewGuid().ToString()];

        Mock<IWebSearchEngineConnector> connectorMock = new();
        connectorMock.Setup(c => c.SearchAsync<string>(It.IsAny<string>(), It.IsAny<int>(), It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        WebSearchEnginePlugin target = new(connectorMock.Object);

        string anyQuery = Guid.NewGuid().ToString();

        // Act
        await target.SearchAsync(anyQuery);

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task GetSearchResultsSucceedsAsync()
    {
        // Arrange
        IEnumerable<WebPage> expected = [];

        Mock<IWebSearchEngineConnector> connectorMock = new();
        connectorMock.Setup(c => c.SearchAsync<WebPage>(It.IsAny<string>(), It.IsAny<int>(), It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        WebSearchEnginePlugin target = new(connectorMock.Object);

        string anyQuery = Guid.NewGuid().ToString();

        // Act
        await target.GetSearchResultsAsync(anyQuery);

        // Assert
        connectorMock.VerifyAll();
    }
}
