// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Moq;
using Xunit;
using static Microsoft.SemanticKernel.Skills.MsGraph.EmailSkill;

namespace SemanticKernel.Skills.UnitTests.MsGraph;

public class EmailSkillTests
{
    private readonly SKContext _context = new();

    [Fact]
    public async Task SendEmailAsyncSucceedsAsync()
    {
        // Arrange
        Mock<IEmailConnector> connectorMock = new();
        connectorMock.Setup(c => c.SendEmailAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string[]>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        EmailSkill target = new(connectorMock.Object);

        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        string anyRecipient = Guid.NewGuid().ToString();

        this._context.Variables.Set(Parameters.Recipients, anyRecipient);
        this._context.Variables.Set(Parameters.Subject, anySubject);

        // Act
        await target.SendEmailAsync(anyContent, anyRecipient, anySubject);

        // Assert
        Assert.False(this._context.ErrorOccurred);
        connectorMock.VerifyAll();
    }

    [Fact]
    public async Task SendEmailAsyncNoRecipientFailsAsync()
    {
        // Arrange
        Mock<IEmailConnector> connectorMock = new();
        EmailSkill target = new(connectorMock.Object);

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
        EmailSkill target = new(connectorMock.Object);

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

        EmailSkill target = new(connectorMock.Object);

        // Act
        string actual = await target.GetMyEmailAddressAsync();

        // Assert
        Assert.Equal(anyEmailAddress, actual);
        Assert.False(this._context.ErrorOccurred);
        connectorMock.VerifyAll();
    }
}
