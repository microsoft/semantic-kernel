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
        IEnumerable<string> expected = new[] { Guid.NewGuid().ToString() };

        Mock<IWebSearchEngineConnector> connectorMock = new();
        connectorMock.Setup(c => c.SearchAsync(It.IsAny<string>(), It.IsAny<int>(), It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        WebSearchEnginePlugin target = new(connectorMock.Object);

        string anyQuery = Guid.NewGuid().ToString();

        // Act
        await target.SearchAsync(anyQuery);

        // Assert
        connectorMock.VerifyAll();
    }
}
