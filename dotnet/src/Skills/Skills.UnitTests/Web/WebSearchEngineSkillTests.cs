// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.Web;
using Moq;
using SemanticKernel.Skills.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Skills.UnitTests.Web;

public sealed class WebSearchEngineSkillTests : IDisposable
{
    private readonly SKContext _context;
    private readonly XunitLogger<SKContext> _logger;

    public WebSearchEngineSkillTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<SKContext>(output);
        this._context = new SKContext(logger: this._logger);
    }

    [Fact]
    public async Task SearchAsyncSucceedsAsync()
    {
        // Arrange
        IEnumerable<string> expected = new[] { Guid.NewGuid().ToString() };

        Mock<IWebSearchEngineConnector> connectorMock = new();
        connectorMock.Setup(c => c.SearchAsync(It.IsAny<string>(), It.IsAny<int>(), It.IsAny<int>(), It.IsAny<CancellationToken>()))
            .ReturnsAsync(expected);

        WebSearchEngineSkill target = new(connectorMock.Object);

        string anyQuery = Guid.NewGuid().ToString();

        // Act
        await target.SearchAsync(anyQuery);

        // Assert
        Assert.False(this._context.ErrorOccurred);
        connectorMock.VerifyAll();
    }

    public void Dispose()
    {
        this._logger.Dispose();
    }
}
