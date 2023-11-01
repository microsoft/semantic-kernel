// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.MsGraph;
using Moq;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.MsGraph;

public class OrganizationHierarchyPluginTests
{
    [Fact]
    public async Task GetMyDirectReportsEmailAsyncSucceedsAsync()
    {
        // Arrange
        string[] anyDirectReportsEmail = { Guid.NewGuid().ToString(), Guid.NewGuid().ToString() };
        Mock<IOrganizationHierarchyConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetDirectReportsEmailAsync(It.IsAny<CancellationToken>())).ReturnsAsync(anyDirectReportsEmail);
        OrganizationHierarchyPlugin target = new(connectorMock.Object);

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
        OrganizationHierarchyPlugin target = new(connectorMock.Object);

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
        OrganizationHierarchyPlugin target = new(connectorMock.Object);

        // Act
        string actual = await target.GetMyManagerNameAsync();

        // Assert
        Assert.Equal(anyManagerName, actual);
        connectorMock.VerifyAll();
    }
}
