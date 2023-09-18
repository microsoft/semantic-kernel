// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Plugins.MsGraph;
using Moq;
using Xunit;

namespace SemanticKernel.Plugins.UnitTests.MsGraph;

public class EmailPluginTests
{
    [Fact]
    public async Task SendEmailAsyncSucceedsAsync()
    {
        // Arrange
        Mock<IEmailConnector> connectorMock = new();
        connectorMock.Setup(c => c.SendEmailAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string[]>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        EmailPlugin target = new(connectorMock.Object);

        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        string anyRecipient = Guid.NewGuid().ToString();

        // Act
        await target.SendEmailAsync(anyContent, anyRecipient, anySubject);

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task SendEmailAsyncNoRecipientFailsAsync()
    {
        // Arrange
        Mock<IEmailConnector> connectorMock = new();
        EmailPlugin target = new(connectorMock.Object);

        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();

        // Act/Assert
        await Assert.ThrowsAnyAsync<ArgumentException>(() =>
            target.SendEmailAsync(anyContent, null!, anySubject));

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task SendEmailAsyncNoSubjectFailsAsync()
    {
        // Arrange
        Mock<IEmailConnector> connectorMock = new();
        EmailPlugin target = new(connectorMock.Object);

        string anyContent = Guid.NewGuid().ToString();
        string anyRecipient = Guid.NewGuid().ToString();

        // Act/Assert
        await Assert.ThrowsAnyAsync<ArgumentException>(() =>
            target.SendEmailAsync(anyContent, anyRecipient, null!));

        // Assert
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task GetMyEmailAddressAsyncSucceedsAsync()
    {
        // Arrange
        string anyEmailAddress = Guid.NewGuid().ToString();
        Mock<IEmailConnector> connectorMock = new();
        connectorMock.Setup(c => c.GetMyEmailAddressAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(anyEmailAddress);

        EmailPlugin target = new(connectorMock.Object);

        // Act
        string actual = await target.GetMyEmailAddressAsync();

        // Assert
        Assert.Equal(anyEmailAddress, actual);
        connectorMock.VerifyAll();
    }
}
