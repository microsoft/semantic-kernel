// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Contains tests for the <see cref="ConversationStateExtension"/> class.
/// </summary>
public class ConversationStateExtensionTests
{
    [Fact]
    public void AIFunctionsBaseImplementationIsEmpty()
    {
        // Arrange.
        var mockExtension = new Mock<ConversationStateExtension>() { CallBase = true };

        // Act.
        var functions = mockExtension.Object.AIFunctions;

        // Assert.
        Assert.NotNull(functions);
        Assert.Empty(functions);
    }

    [Fact]
    public async Task OnThreadCreatedBaseImplementationSucceeds()
    {
        // Arrange.
        var mockExtension = new Mock<ConversationStateExtension>() { CallBase = true };

        // Act & Assert.
        await mockExtension.Object.OnThreadCreatedAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnNewMessageBaseImplementationSucceeds()
    {
        // Arrange.
        var mockExtension = new Mock<ConversationStateExtension>() { CallBase = true };
        var newMessage = new ChatMessage(ChatRole.User, "Hello");

        // Act & Assert.
        await mockExtension.Object.OnNewMessageAsync("threadId", newMessage, CancellationToken.None);
    }

    [Fact]
    public async Task OnThreadDeleteBaseImplementationSucceeds()
    {
        // Arrange.
        var mockExtension = new Mock<ConversationStateExtension>() { CallBase = true };

        // Act & Assert.
        await mockExtension.Object.OnThreadDeleteAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnSuspendBaseImplementationSucceeds()
    {
        // Arrange.
        var mockExtension = new Mock<ConversationStateExtension>() { CallBase = true };

        // Act & Assert.
        await mockExtension.Object.OnSuspendAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnResumeBaseImplementationSucceeds()
    {
        // Arrange.
        var mockExtension = new Mock<ConversationStateExtension>() { CallBase = true };

        // Act & Assert.
        await mockExtension.Object.OnResumeAsync("threadId", CancellationToken.None);
    }
}
