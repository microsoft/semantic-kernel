// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Contains tests for the <see cref="AIContextProvider"/> class.
/// </summary>
public class AIContextBehaviorTests
{
    [Fact]
    public async Task OnThreadCreatedBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextProvider>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.ConversationCreatedAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnNewMessageBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextProvider>() { CallBase = true };
        var newMessage = new ChatMessage(ChatRole.User, "Hello");

        // Act & Assert.
        await mockPart.Object.MessageAddingAsync("threadId", newMessage, CancellationToken.None);
    }

    [Fact]
    public async Task OnThreadDeleteBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextProvider>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.ConversationDeletingAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnSuspendBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextProvider>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.SuspendingAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnResumeBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextProvider>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.ResumingAsync("threadId", CancellationToken.None);
    }
}
