// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Moq;
using SemanticKernel.Skills.UnitTests.XunitHelpers;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.Skills.UnitTests.MsGraph;

public class OrganizationHierarchySkillTests : IDisposable
{
    private readonly XunitLogger<SKContext> _logger;
    private readonly SKContext _context;
    private bool _disposedValue = false;

    public OrganizationHierarchySkillTests(ITestOutputHelper output)
    {
        this._logger = new XunitLogger<SKContext>(output);
        this._context = new SKContext(logger: this._logger, cancellationToken: CancellationToken.None);
    }

    [Fact]
    public async Task GetMyDirectReportsEmailAsyncSucceedsAsync()
    {
        // Arrange
        string[] anyDirectReportsEmail = { Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };
        Mock<IOrganizationHierarchyConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetDirectReportsEmailAsync(It.IsAny<CancellationToken>())).ReturnsAsync(anyDirectReportsEmail);
        OrganizationHierarchySkill target = new(connectorMock.Object);

        // Act
        string actual = await target.GetMyDirectReportsEmailAsync();

        // Assert
        var emails = JsonSerializer.Deserialize<IEnumerable<string>>(actual);
        Assert.NotNull(emails);
        foreach (string directReportEmail in anyDirectReportsEmail)
        {
            Assert.Contains(directReportEmail, emails);
        }

        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task GetMyManagerEmailAsyncSucceedsAsync()
    {
        // Arrange
        string anyManagerEmail = Guid.NewGuid().ToString();
        Mock<IOrganizationHierarchyConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetManagerEmailAsync(It.IsAny<CancellationToken>())).ReturnsAsync(anyManagerEmail);
        OrganizationHierarchySkill target = new(connectorMock.Object);

        // Act
        string actual = await target.GetMyManagerEmailAsync();

        // Assert
        Assert.Equal(anyManagerEmail, actual);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task GetMyManagerNameAsyncSucceedsAsync()
    {
        // Arrange
        string anyManagerName = Guid.NewGuid().ToString();
        Mock<IOrganizationHierarchyConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetManagerNameAsync(It.IsAny<CancellationToken>())).ReturnsAsync(anyManagerName);
        OrganizationHierarchySkill target = new(connectorMock.Object);

        // Act
        string actual = await target.GetMyManagerNameAsync();

        // Assert
        Assert.Equal(anyManagerName, actual);
        connectorMock.VerifyAll();
    }

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._logger.Dispose();
            }

            this._disposedValue = true;
        }
    }

    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }
}
