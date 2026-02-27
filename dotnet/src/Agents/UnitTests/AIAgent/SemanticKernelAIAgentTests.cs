// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents;
using Microsoft.SemanticKernel.ChatCompletion;
using Moq;
using Xunit;
using MAAI = Microsoft.Agents.AI;
using MEAI = Microsoft.Extensions.AI;

namespace SemanticKernel.Agents.UnitTests.AIAgent;

public sealed class SemanticKernelAIAgentTests
{
    [Fact]
    public void Constructor_Succeeds()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act
        var adapter = new SemanticKernelAIAgent(agentMock.Object, ThreadFactory, ThreadDeserializationFactory, ThreadSerializer);

        // Assert
        Assert.IsType<SemanticKernelAIAgent>(adapter);
    }

    [Fact]
    public void Constructor_WithNullSemanticKernelAgent_ThrowsArgumentNullException()
    {
        // Arrange
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new SemanticKernelAIAgent(null!, ThreadFactory, ThreadDeserializationFactory, ThreadSerializer));
    }

    [Fact]
    public void Constructor_WithNullThreadFactory_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new SemanticKernelAIAgent(agentMock.Object, null!, ThreadDeserializationFactory, ThreadSerializer));
    }

    [Fact]
    public void Constructor_WithNullThreadDeserializationFactory_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new SemanticKernelAIAgent(agentMock.Object, ThreadFactory, null!, ThreadSerializer));
    }

    [Fact]
    public void Constructor_WithNullThreadSerializer_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        AgentThread ThreadFactory() => Mock.Of<AgentThread>();
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => Mock.Of<AgentThread>();

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => new SemanticKernelAIAgent(agentMock.Object, ThreadFactory, ThreadDeserializationFactory, null!));
    }

    [Fact]
    public void DeserializeThread_ReturnsSemanticKernelAIAgentThread()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;
        AgentThread ThreadDeserializationFactory(JsonElement e, JsonSerializerOptions? o) => expectedThread;
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => expectedThread, ThreadDeserializationFactory, ThreadSerializer);
        var json = JsonElement.Parse("{}");

        // Act
        var result = adapter.DeserializeThread(json);

        // Assert
        Assert.IsType<SemanticKernelAIAgentThread>(result);
    }

    [Fact]
    public void GetNewThread_ReturnsSemanticKernelAIAgentThread()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        JsonElement ThreadSerializer(AgentThread t, JsonSerializerOptions? o) => default;
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => expectedThread, (e, o) => expectedThread, ThreadSerializer);

        // Act
        var result = adapter.GetNewThread();

        // Assert
        Assert.IsType<SemanticKernelAIAgentThread>(result);
        Assert.Equal(expectedThread, ((SemanticKernelAIAgentThread)result).InnerThread);
    }

    [Fact]
    public void DeserializeThread_CallsDeserializationFactory()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        var factoryCallCount = 0;

        AgentThread DeserializationFactory(JsonElement e, JsonSerializerOptions? o)
        {
            factoryCallCount++;
            return expectedThread;
        }

        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => expectedThread, DeserializationFactory, (t, o) => default);
        var json = JsonElement.Parse("{}");

        // Act
        var result = adapter.DeserializeThread(json);

        // Assert
        Assert.Equal(1, factoryCallCount);
        Assert.IsType<SemanticKernelAIAgentThread>(result);
    }

    [Fact]
    public void GetNewThread_CallsThreadFactory()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var expectedThread = Mock.Of<AgentThread>();
        var factoryCallCount = 0;

        AgentThread ThreadFactory()
        {
            factoryCallCount++;
            return expectedThread;
        }

        var adapter = new SemanticKernelAIAgent(agentMock.Object, ThreadFactory, (e, o) => expectedThread, (t, o) => default);

        // Act
        var result = adapter.GetNewThread();

        // Assert
        Assert.Equal(1, factoryCallCount);
        Assert.IsType<SemanticKernelAIAgentThread>(result);
    }

    [Fact]
    public void Properties_ReflectInnerAgentProperties()
    {
        // Arrange
        var concreteAgent = new TestAgent
        {
            Id = "test-agent-id",
            Name = "Test Agent Name",
            Description = "Test Agent Description"
        };

        var adapter = new SemanticKernelAIAgent(concreteAgent, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act & Assert
        Assert.Equal("test-agent-id", adapter.Id);
        Assert.Equal("Test Agent Name", adapter.Name);
        Assert.Equal("Test Agent Description", adapter.Description);
    }

    [Fact]
    public async Task Run_CallsInnerAgentAsync()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var innerThread = threadMock.Object;
        var agentMock = new Mock<Agent>();
        agentMock.Setup(a => a.InvokeAsync(
            It.IsAny<List<ChatMessageContent>>(),
            It.IsAny<AgentThread>(),
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()))
            .Returns(MockInvokeAsync);
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> MockInvokeAsync(ICollection<ChatMessageContent> messages,
            AgentThread? thread = null,
            AgentInvokeOptions? options = null,
            [EnumeratorCancellation] CancellationToken cancellationToken = default)
        {
            var message = new ChatMessageContent(AuthorRole.Assistant, "Final response");
            await options!.OnIntermediateMessage!.Invoke(message);
            yield return new AgentResponseItem<ChatMessageContent>(message, innerThread);
        }

        var thread = new SemanticKernelAIAgentThread(innerThread, (t, o) => default);

        // Act
        var result = await adapter.RunAsync("Input text", thread);

        // Assert
        Assert.IsType<MAAI.AgentRunResponse>(result);
        Assert.Equal("Final response", result.Text);
        agentMock.Verify(a => a.InvokeAsync(
            It.Is<List<ChatMessageContent>>(x => x.First().Content == "Input text"),
            innerThread,
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task RunStreaming_CallsInnerAgentAsync()
    {
        // Arrange
        var threadMock = new Mock<AgentThread>();
        var innerThread = threadMock.Object;
        var agentMock = new Mock<Agent>();
        agentMock.Setup(a => a.InvokeStreamingAsync(
            It.IsAny<List<ChatMessageContent>>(),
            It.IsAny<AgentThread>(),
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()))
            .Returns(GetAsyncEnumerable());
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        async IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> GetAsyncEnumerable()
        {
            yield return new AgentResponseItem<StreamingChatMessageContent>(new StreamingChatMessageContent(AuthorRole.Assistant, "Final response"), innerThread);
        }

        var thread = new SemanticKernelAIAgentThread(innerThread, (t, o) => default);

        // Act
        var results = await adapter.RunStreamingAsync("Input text", thread).ToListAsync();

        // Assert
        Assert.IsType<MAAI.AgentRunResponseUpdate>(results.First());
        Assert.Equal("Final response", results.First().Text);
        agentMock.Verify(a => a.InvokeStreamingAsync(
            It.Is<List<ChatMessageContent>>(x => x.First().Content == "Input text"),
            innerThread,
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()), Times.Once);
    }

    [Fact]
    public async Task RunAsync_RemovesDuplicateTextContentInToolMessage()
    {
        // Arrange
        var innerThread = Mock.Of<AgentThread>();
        var agentMock = new Mock<Agent>();
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => innerThread, (e, o) => innerThread, (t, o) => default);

        agentMock.Setup(a => a.InvokeAsync(
            It.IsAny<List<ChatMessageContent>>(),
            It.IsAny<AgentThread>(),
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()))
            .Returns((List<ChatMessageContent> msgs, AgentThread thread, AgentInvokeOptions opts, CancellationToken ct) => GetEnumerableWithDuplicateToolMessage(thread, opts));

        async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> GetEnumerableWithDuplicateToolMessage(AgentThread thread, AgentInvokeOptions opts)
        {
            // Tool message with duplicate text + function result
            var toolMessage = new ChatMessageContent(AuthorRole.Tool, "RESULT");
            toolMessage.Items.Add(new FunctionResultContent(functionName: "Fn", result: "RESULT"));
            await opts.OnIntermediateMessage!.Invoke(toolMessage);

            // Final assistant message
            var final = new ChatMessageContent(AuthorRole.Assistant, "done");
            yield return new AgentResponseItem<ChatMessageContent>(final, thread);
        }

        var threadWrapper = new SemanticKernelAIAgentThread(innerThread, (t, o) => default);

        // Act
        var response = await adapter.RunAsync("input", threadWrapper);

        // Assert
        // Use reflection to inspect Messages collection inside AgentRunResponse
        var messages = response.Messages;
        var contents = messages.First().Contents;
        Assert.Single(contents); // Duplicate text content should have been removed
        Assert.IsType<MEAI.FunctionResultContent>(contents.First());
    }

    [Fact]
    public async Task RunAsync_DoesNotRemoveTextContentWhenDifferent()
    {
        // Arrange
        var innerThread = Mock.Of<AgentThread>();
        var agentMock = new Mock<Agent>();
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => innerThread, (e, o) => innerThread, (t, o) => default);

        agentMock.Setup(a => a.InvokeAsync(
            It.IsAny<List<ChatMessageContent>>(),
            It.IsAny<AgentThread>(),
            It.IsAny<AgentInvokeOptions>(),
            It.IsAny<CancellationToken>()))
            .Returns((List<ChatMessageContent> msgs, AgentThread thread, AgentInvokeOptions opts, CancellationToken ct) => GetEnumerableWithNonDuplicateToolMessage(thread, opts));

        async IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> GetEnumerableWithNonDuplicateToolMessage(AgentThread thread, AgentInvokeOptions opts)
        {
            // Tool message with text + function result differing
            var toolMessage = new ChatMessageContent(AuthorRole.Tool, "TEXT");
            toolMessage.Items.Add(new FunctionResultContent(functionName: "Fn", result: "DIFFERENT"));
            await opts.OnIntermediateMessage!.Invoke(toolMessage);

            var final = new ChatMessageContent(AuthorRole.Assistant, "done");
            yield return new AgentResponseItem<ChatMessageContent>(final, thread);
        }

        var threadWrapper = new SemanticKernelAIAgentThread(innerThread, (t, o) => default);

        // Act
        var response = await adapter.RunAsync("input", threadWrapper);

        // Assert
        var messages = response.Messages;
        var contents = messages.First().Contents;
        Assert.Equal(2, contents.Count); // Both contents should remain
        Assert.IsType<MEAI.TextContent>(contents.First());
        Assert.IsType<MEAI.FunctionResultContent>(contents.Last());
    }

    [Fact]
    public void GetService_WithKernelType_ReturnsKernel()
    {
        // Arrange
        var kernel = new Kernel();
        var fakeAgent = new TestAgent() { Kernel = kernel };

        var adapter = new SemanticKernelAIAgent(fakeAgent, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act
        var result = adapter.GetService(typeof(Kernel));

        // Assert
        Assert.Same(kernel, result);
    }

    [Fact]
    public void GetService_WithKernelTypeAndServiceKey_ReturnsNull()
    {
        // Arrange
        var kernel = new Kernel();
        var fakeAgent = new TestAgent() { Kernel = kernel };
        var adapter = new SemanticKernelAIAgent(fakeAgent, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);
        var serviceKey = new object();

        // Act
        var result = adapter.GetService(typeof(Kernel), serviceKey);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetService_WithAgentType_ReturnsInnerAgent()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act
        var result = adapter.GetService(typeof(Agent));

        // Assert
        Assert.Same(agentMock.Object, result);
    }

    [Fact]
    public void GetService_WithAgentTypeAndServiceKey_ReturnsNull()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);
        var serviceKey = new object();

        // Act
        var result = adapter.GetService(typeof(Agent), serviceKey);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetService_WithNonAgentType_ReturnsNull()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act
        var result = adapter.GetService(typeof(string));

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void GetService_WithNullType_ThrowsArgumentNullException()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act & Assert
        Assert.Throws<ArgumentNullException>(() => adapter.GetService(null!));
    }

    [Fact]
    public void GetService_WithBaseClassType_ReturnsInnerAgent()
    {
        // Arrange
        var concreteAgent = new TestAgent();
        var adapter = new SemanticKernelAIAgent(concreteAgent, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act
        var result = adapter.GetService(typeof(Agent));

        // Assert
        Assert.Same(concreteAgent, result);
    }

    [Fact]
    public void GetService_WithDerivedType_ReturnsInnerAgentWhenMatches()
    {
        // Arrange
        var concreteAgent = new TestAgent();
        var adapter = new SemanticKernelAIAgent(concreteAgent, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act
        var result = adapter.GetService(typeof(TestAgent));

        // Assert
        Assert.Same(concreteAgent, result);
    }

    [Fact]
    public void GetService_WithIncompatibleDerivedType_ReturnsNull()
    {
        // Arrange
        var agentMock = new Mock<Agent>();
        var adapter = new SemanticKernelAIAgent(agentMock.Object, () => Mock.Of<AgentThread>(), (e, o) => Mock.Of<AgentThread>(), (t, o) => default);

        // Act
        var result = adapter.GetService(typeof(TestAgent));

        // Assert
        Assert.Null(result);
    }

    private sealed class TestAgent : Agent
    {
        public override IAsyncEnumerable<AgentResponseItem<ChatMessageContent>> InvokeAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        public override IAsyncEnumerable<AgentResponseItem<StreamingChatMessageContent>> InvokeStreamingAsync(ICollection<ChatMessageContent> messages, AgentThread? thread = null, AgentInvokeOptions? options = null, CancellationToken cancellationToken = default)
        {
            throw new NotImplementedException();
        }

        protected internal override Task<AgentChannel> CreateChannelAsync(CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }

        protected internal override IEnumerable<string> GetChannelKeys()
        {
            throw new NotImplementedException();
        }

        protected internal override Task<AgentChannel> RestoreChannelAsync(string channelState, CancellationToken cancellationToken)
        {
            throw new NotImplementedException();
        }
    }
}
