// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Skills.MsGraph;
using Moq;
using Xunit;
using static Microsoft.SemanticKernel.Skills.MsGraph.EmailSkill;

namespace SemanticKernel.Skills.UnitTests.MsGraph;

public class EmailSkillTests
{
    private readonly SKContext _context = new SKContext(new ContextVariables(), NullMemory.Instance, null, NullLogger.Instance);

    [Fact]
    public async Task SendEmailAsyncSucceedsAsync()
    {
        // Arrange
        Mock<IEmailAdapter> adapterMock = new();
        adapterMock.Setup(c => c.SendEmailAsync(It.IsAny<string>(), It.IsAny<string>(), It.IsAny<string[]>(), It.IsAny<CancellationToken>()))
            .Returns(Task.CompletedTask);

        EmailSkill target = new(adapterMock.Object);

        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();
        string anyRecipient = Guid.NewGuid().ToString();

        this._context.Variables.Set(Parameters.Recipients, anyRecipient);
        this._context.Variables.Set(Parameters.Subject, anySubject);

        // Act
        await target.SendEmailAsync(anyContent, this._context);

        // Assert
        Assert.False(this._context.ErrorOccurred);
        adapterMock.VerifyAll();
    }

    [Fact]
    public async Task SendEmailAsyncNoRecipientFailsAsync()
    {
        // Arrange
        Mock<IEmailAdapter> adapterMock = new();
        EmailSkill target = new(adapterMock.Object);

        string anyContent = Guid.NewGuid().ToString();
        string anySubject = Guid.NewGuid().ToString();

        this._context.Variables.Set(Parameters.Subject, anySubject);
        this._context.Variables.Update(anyContent);

        // Act
        await target.SendEmailAsync(anyContent, this._context);

        // Assert
        Assert.True(this._context.ErrorOccurred);
        adapterMock.VerifyAll();
    }

    [Fact]
    public async Task SendEmailAsyncNoSubjectFailsAsync()
    {
        // Arrange
        Mock<IEmailAdapter> adapterMock = new();
        EmailSkill target = new(adapterMock.Object);

        string anyContent = Guid.NewGuid().ToString();
        string anyRecipient = Guid.NewGuid().ToString();

        this._context.Variables.Set(Parameters.Recipients, anyRecipient);
        this._context.Variables.Update(anyContent);

        // Act
        await target.SendEmailAsync(anyContent, this._context);

        // Assert
        Assert.True(this._context.ErrorOccurred);
        adapterMock.VerifyAll();
    }

    [Fact]
    public async Task GetMyEmailAddressAsyncSucceedsAsync()
    {
        // Arrange
        string anyEmailAddress = Guid.NewGuid().ToString();
        Mock<IEmailAdapter> adapterMock = new();
        adapterMock.Setup(c => c.GetMyEmailAddressAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(anyEmailAddress);

        EmailSkill target = new(adapterMock.Object);

        // Act
        string actual = await target.GetMyEmailAddressAsync();

        // Assert
        Assert.Equal(anyEmailAddress, actual);
        Assert.False(this._context.ErrorOccurred);
        adapterMock.VerifyAll();
    }
}
