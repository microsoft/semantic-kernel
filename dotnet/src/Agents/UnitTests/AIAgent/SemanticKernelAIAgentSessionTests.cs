// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AIAgent;

public sealed class SemanticKernelAIAgentSessionTests
{
    [Fact]
    public void Constructor_InitializesProperties()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();

        // Act
        var adapter = new SemanticKernelAIAgentSession(threadMock.Object);

        // Assert
        Assert.Equal(threadMock.Object, adapter.InnerThread);
    }

    // AF 1.0: Serialize_CallsThreadSerializer test removed - serialization moved to agent.
    // See SemanticKernelAIAgentTests for serialization coverage.

    // AF 1.0: Serialize() moved from AgentSession to AIAgent.SerializeSessionCoreAsync().
    // These tests are covered by SemanticKernelAIAgentTests instead.

    [Fact]
    public void GetService_WithAgentThreadType_ReturnsInnerThread()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var adapter = new SemanticKernelAIAgentSession(threadMock.Object);

        // Act
        var result = adapter.GetService(typeof(AgentThread));

        // Assert
        Assert.Same(threadMock.Object, result);
    }

    [Fact]
    public void GetService_WithAgentThreadTypeAndServiceKey_ReturnsNull()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var adapter = new SemanticKernelAIAgentSession(threadMock.Object);
        var serviceKey = new object();

        // Act
        var result = adapter.GetService(typeof(AgentThread), serviceKey);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetService_WithNonAgentThreadType_ReturnsNull()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var adapter = new SemanticKernelAIAgentSession(threadMock.Object);

        // Act
        var result = adapter.GetService(typeof(string));

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetService_WithNullType_ThrowsArgumentNullException()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var adapter = new SemanticKernelAIAgentSession(threadMock.Object);

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => adapter.GetService(null!));
    }

    // AF 1.0: Serialize_WithNullOptions test removed - serialization moved to agent.

    [Fact]
    public void Constructor_WithNullThread_ThrowsArgumentNullException()
    {
        // Arrange & Act
        Assert.Throws<ArgumentNullException>(() => new SemanticKernelAIAgentSession(null!));
    }

    // Constructor_WithNullSerializer test removed: serializer is no longer stored on the session.

    [Fact]
    public void GetService_WithBaseClassType_ReturnsInnerThread()
    {
        // Arrange
        var concreteThread = new TestAgentThread();
        var adapter = new SemanticKernelAIAgentSession(concreteThread);

        // Act
        var result = adapter.GetService(typeof(AgentThread));

        // Assert
        Assert.Same(concreteThread, result);
    }

    [Fact]
    public void GetService_WithDerivedType_ReturnsInnerThreadWhenMatches()
    {
        // Arrange
        var concreteThread = new TestAgentThread();
        var adapter = new SemanticKernelAIAgentSession(concreteThread);

        // Act
        var result = adapter.GetService(typeof(TestAgentThread));

        // Assert
        Assert.Same(concreteThread, result);
    }

    [Fact]
    public void GetService_WithIncompatibleDerivedType_ReturnsNull()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var adapter = new SemanticKernelAIAgentSession(threadMock.Object);

        // Act
        var result = adapter.GetService(typeof(TestAgentThread));

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetService_WithInterfaceType_ReturnsNull()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var adapter = new SemanticKernelAIAgentSession(threadMock.Object);

        // Act
        var result = adapter.GetService(typeof(IServiceProvider));

        // Assert
        Assert.Null(result);
    }

    private sealed class TestAgentThread : AgentThread
    {
        protected override Task<string?> CreateInternalAsync(CancellationToken cancellationToken)
        {
            return Task.FromResult<string?>("test-thread-id");
        }

        protected override Task DeleteInternalAsync(CancellationToken cancellationToken)
        {
            return Task.CompletedTask;
        }

        protected override Task OnNewMessageInternalAsync(ChatMessageContent newMessage, CancellationToken cancellationToken = default)
        {
            return Task.CompletedTask;
        }
    }
}
