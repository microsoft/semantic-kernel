// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.SemanticKernel;
using Moq;
using Xunit;

namespace SemanticKernel.UnitTests.Memory;

/// <summary>
/// Contains tests for the <see cref="AIContextBehavior"/> class.
/// </summary>
public class AIContextBehaviorTests
{
    [Fact]
    public async Task OnThreadCreatedBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextBehavior>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.OnThreadCreatedAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnNewMessageBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextBehavior>() { CallBase = true };
        var newMessage = new ChatMessage(ChatRole.User, "Hello");

        // Act & Assert.
        await mockPart.Object.OnNewMessageAsync("threadId", newMessage, CancellationToken.None);
    }

    [Fact]
    public async Task OnThreadDeleteBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextBehavior>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.OnThreadDeleteAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnSuspendBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextBehavior>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.OnSuspendAsync("threadId", CancellationToken.None);
    }

    [Fact]
    public async Task OnResumeBaseImplementationSucceeds()
    {
        // Arrange.
        var mockPart = new Mock<AIContextBehavior>() { CallBase = true };

        // Act & Assert.
        await mockPart.Object.OnResumeAsync("threadId", CancellationToken.None);
    }
}
