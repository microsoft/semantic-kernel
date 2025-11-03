// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Moq;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.AIAgent;

public sealed class SemanticKernelAIAgentThreadTests
{
    [Fact]
    public void Constructor_InitializesProperties()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act
        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, ThreadSerializer);

        // Assert
        Assert.Equal(threadMock.Object, adapter.InnerThread);
    }

    [Fact]
    public void Serialize_CallsThreadSerializer()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var serializerCallCount = 0;
        var expectedJsonElement = JsonDocument.Parse("{\"test\": \"value\"}").RootElement;

        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o)
        {
            serializerCallCount++;
            Assert.Same(threadMock.Object, t);
            return expectedJsonElement;
        }

        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, ThreadSerializer);

        // Act
        var result = adapter.Serialize();

        // Assert
        Assert.Equal(1, serializerCallCount);
        Assert.Equal(expectedJsonElement.ToString(), result.ToString());
    }

    [Fact]
    public void Serialize_WithJsonSerializerOptions_PassesOptionsToSerializer()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var expectedOptions = new JsonSerializerOptions();
        JsonSerializerOptions? capturedOptions = null;

        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o)
        {
            capturedOptions = o;
            return default;
        }

        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, ThreadSerializer);

        // Act
        adapter.Serialize(expectedOptions);

        // Assert
        Assert.Same(expectedOptions, capturedOptions);
    }

    [Fact]
    public void GetService_WithAgentThreadType_ReturnsInnerThread()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, (t, o) => default);

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
        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, (t, o) => default);
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
        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, (t, o) => default);

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
        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, (t, o) => default);

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => adapter.GetService(null!));
    }

    [Fact]
    public void Serialize_WithNullOptions_CallsSerializerWithNull()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        JsonSerializerOptions? capturedOptions = new();

        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o)
        {
            capturedOptions = o;
            return default;
        }

        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, ThreadSerializer);

        // Act
        adapter.Serialize(null);

        // Assert
        Assert.Null(capturedOptions);
    }

    [Fact]
    public void Constructor_WithNullThread_ThrowsArgumentNullException()
    {
        // Arrange & Act
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;
        Assert.Throws<ArgumentNullException>(() => new SemanticKernelAIAgentThread(null!, ThreadSerializer));
    }

    [Fact]
    public void Constructor_WithNullSerializer_ThrowsArgumentNullException()
    {
        // Arrange & Act
        var threadMock = new Mock<AgentThread>();
        Assert.Throws<ArgumentNullException>(() => new SemanticKernelAIAgentThread(threadMock.Object, null!));
    }

    [Fact]
    public void GetService_WithBaseClassType_ReturnsInnerThread()
    {
        // Arrange
        var concreteThread = new TestAgentThread();
        var adapter = new SemanticKernelAIAgentThread(concreteThread, (t, o) => default);

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
        var adapter = new SemanticKernelAIAgentThread(concreteThread, (t, o) => default);

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
        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, (t, o) => default);

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
        var adapter = new SemanticKernelAIAgentThread(threadMock.Object, (t, o) => default);

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
