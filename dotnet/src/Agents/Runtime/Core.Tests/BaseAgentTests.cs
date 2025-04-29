// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using FluentAssertions;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Moq;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Tests;

[Trait("Category", "Unit")]
public class BaseAgentTests
{
    [Fact]
    public void Constructor_InitializesActivitySource_Correctly()
    {
        BaseAgent.TraceSource.Name.Should().Be("Microsoft.SemanticKernel.Agents.Runtime");
    }

    [Fact]
    public void Constructor_InitializesProperties_Correctly()
    {
        // Arrange
        using ILoggerFactory loggerFactory = LoggerFactory.Create(_ => { });
        ILogger<TestAgentA> logger = loggerFactory.CreateLogger<TestAgentA>();
        AgentId agentId = new("TestType", "TestKey");
        const string description = "Test Description";
        Mock<IAgentRuntime> runtimeMock = new();

        // Act
        TestAgentA agent = new(agentId, runtimeMock.Object, description, logger);

        // Assert
        agent.Id.Should().Be(agentId);
        agent.Metadata.Type.Should().Be(agentId.Type);
        agent.Metadata.Key.Should().Be(agentId.Key);
        agent.Metadata.Description.Should().Be(description);
        agent.Logger.Should().Be(logger);
    }

    [Fact]
    public void Constructor_WithNoLogger_CreatesNullLogger()
    {
        // Arrange
        AgentId agentId = new("TestType", "TestKey");
        string description = "Test Description";
        Mock<IAgentRuntime> runtimeMock = new();

        // Act
        TestAgentA agent = new(agentId, runtimeMock.Object, description);

        // Assert
        agent.Logger.Should().Be(NullLogger.Instance);
    }

    [Fact]
    public async Task OnMessageAsync_WithoutMatchingHandler()
    {
        // Arrange
        Mock<IAgentRuntime> runtimeMock = new();
        AgentId agentId = new("TestType", "TestKey");
        TestAgentA agent = new(agentId, runtimeMock.Object, "Test Agent");
        MessageContext context = new(CancellationToken.None);

        // Act
        const string message = "This is a TestMessage";
        object? result = await agent.OnMessageAsync(message, context);

        // Assert
        result.Should().BeNull();
        agent.ReceivedMessages.Should().BeEmpty();
    }

    [Fact]
    public async Task OnMessageAsync_WithMatchingHandler_NoResult()
    {
        // Arrange
        Mock<IAgentRuntime> runtimeMock = new();
        AgentId agentId = new("TestType", "TestKey");
        TestAgentA agent = new(agentId, runtimeMock.Object, "Test Agent");

        // Act
        TestMessage message = new() { Content = "Hello World" };
        MessageContext context = new(CancellationToken.None);
        object? result = await agent.OnMessageAsync(message, context);

        // Assert
        result.Should().BeNull();
        agent.ReceivedMessages.Should().ContainSingle();
    }

    [Fact]
    public async Task OnMessageAsync_WithMatchingHandler_HasResult()
    {
        // Arrange
        Mock<IAgentRuntime> runtimeMock = new();
        AgentId agentId = new("TestType", "TestKey");
        TestAgentB agent = new(agentId, runtimeMock.Object);

        // Act
        TestMessage message = new() { Content = "Hello World" };
        MessageContext context = new(CancellationToken.None);
        object? result = await agent.OnMessageAsync(message, context);

        // Assert
        result.Should().Be(message.Content);
        agent.ReceivedMessages.Should().ContainSingle();
        agent.ReceivedMessages[0].Should().Contain(message.Content);
    }

    [Fact]
    public async Task CloseAsync_ReturnsCompletedTask()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        AgentId agentId = new("TestType", "TestKey");
        TestAgentA agent = new(agentId, runtime, "Test Agent");

        // Act
        await agent.CloseAsync();

        // Assert
        agent.IsClosed.Should().BeTrue();
    }

    [Fact]
    public async Task PublishMessageAsync_Received()
    {
        // Arrange
        ServiceProvider services = new ServiceCollection().BuildServiceProvider();
        await using InProcessRuntime runtime = new();
        TopicId topic = new("TestTopic");
        AgentType senderType = nameof(TestAgentC);
        AgentType receiverType = nameof(TestAgentB);
        await runtime.RegisterAgentTypeAsync<TestAgentB>(receiverType, services);
        await runtime.AddSubscriptionAsync(new TypeSubscription(topic.Type, receiverType));
        AgentId receiverId = await runtime.GetAgentAsync(receiverType, lazy: false);
        await runtime.RegisterAgentTypeAsync<TestAgentC>(senderType, services, [topic]);
        AgentId senderId = await runtime.GetAgentAsync(senderType, lazy: false);

        // Act
        await runtime.StartAsync();
        TestMessage message = new() { Content = "Hello World" };
        try
        {
            await runtime.SendMessageAsync(message, senderId);
        }
        finally
        {
            await runtime.RunUntilIdleAsync();
        }

        // Assert
        await VerifyMessageHandled(runtime, senderId, message.Content);
        await VerifyMessageHandled(runtime, receiverId, message.Content);
    }

    [Fact]
    public async Task SendMessageAsync_Received()
    {
        // Arrange
        ServiceProvider services = new ServiceCollection().BuildServiceProvider();
        await using InProcessRuntime runtime = new();
        AgentType senderType = nameof(TestAgentD);
        AgentType receiverType = nameof(TestAgentB);
        await runtime.RegisterAgentTypeAsync<TestAgentB>(receiverType, services);
        AgentId receiverId = await runtime.GetAgentAsync(receiverType, lazy: false);
        await runtime.RegisterAgentTypeAsync<TestAgentD>(senderType, services, [receiverId]);
        AgentId senderId = await runtime.GetAgentAsync(senderType, lazy: false);

        // Act
        await runtime.StartAsync();
        TestMessage message = new() { Content = "Hello World" };
        try
        {
            await runtime.SendMessageAsync(message, senderId);
        }
        finally
        {
            await runtime.RunUntilIdleAsync();
        }

        // Assert
        await VerifyMessageHandled(runtime, senderId, message.Content);
        await VerifyMessageHandled(runtime, receiverId, message.Content);
    }

    private static async Task VerifyMessageHandled(InProcessRuntime runtime, AgentId agentId, string expectedContent)
    {
        TestAgent agent = await runtime.TryGetUnderlyingAgentInstanceAsync<TestAgent>(agentId);
        agent.ReceivedMessages.Should().ContainSingle();
        agent.ReceivedMessages[0].Should().Be(expectedContent);
    }

    [Fact]
    public async Task SaveStateAsync_ReturnsEmptyJsonElement()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        AgentId agentId = new("TestType", "TestKey");
        TestAgentA agent = new(agentId, runtime, "Test Agent");

        // Act
        var state = await agent.SaveStateAsync();

        // Assert
        state.ValueKind.Should().Be(JsonValueKind.Object);
        state.EnumerateObject().Count().Should().Be(0);
    }

    [Fact]
    public async Task LoadStateAsync_WithValidState_HandlesStateCorrectly()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        AgentId agentId = new("TestType", "TestKey");
        TestAgentA agent = new(agentId, runtime, "Test Agent");

        JsonElement state = JsonDocument.Parse("{ }").RootElement;

        // Act
        await agent.LoadStateAsync(state);

        // Assert
        // BaseAgent's default implementation just accepts any state without error
        // This is primarily testing that the default method doesn't throw exceptions
    }

    [Fact]
    public async Task GetAgentAsync_WithValidType_ReturnsAgentId()
    {
        // Arrange
        ServiceProvider services = new ServiceCollection().BuildServiceProvider();
        await using InProcessRuntime runtime = new();
        AgentType agentType = nameof(TestAgentB);
        await runtime.RegisterAgentTypeAsync<TestAgentB>(agentType, services);

        AgentId callingAgentId = new("CallerType", "CallerKey");
        TestAgentB callingAgent = new(callingAgentId, runtime);

        // Act
        await runtime.StartAsync();
        AgentId? retrievedAgentId = await callingAgent.GetAgentAsync(agentType);

        // Assert
        retrievedAgentId.Should().NotBeNull();
        retrievedAgentId!.Value.Type.Should().Be(agentType.Name);
        retrievedAgentId!.Value.Key.Should().Be(AgentId.DefaultKey);

        // Act
        retrievedAgentId = await callingAgent.GetAgentAsync("badtype");

        // Assert
        retrievedAgentId.Should().BeNull();
    }

    // Custom test message
    private sealed class TestMessage
    {
        public string Content { get; set; } = string.Empty;
    }

    // TestAgent that collects the messages it receives
    protected abstract class TestAgent : BaseAgent
    {
        public List<string> ReceivedMessages { get; } = [];

        protected TestAgent(AgentId id, IAgentRuntime runtime, string description, ILogger? logger = null)
            : base(id, runtime, description, logger)
        {
        }
    }

    private sealed class TestAgentA : TestAgent, IHandle<TestMessage>
    {
        public bool IsClosed { get; private set; }

        public TestAgentA(AgentId id, IAgentRuntime runtime, string description, ILogger<TestAgentA>? logger = null)
            : base(id, runtime, description, logger)
        {
        }

        public ValueTask HandleAsync(TestMessage item, MessageContext messageContext)
        {
            this.ReceivedMessages.Add(item.Content);
            return ValueTask.CompletedTask;
        }

        public override ValueTask CloseAsync()
        {
            this.IsClosed = true;
            return base.CloseAsync();
        }
    }

    // TestAgent that implements handler for TestMessage that produces a result
    private sealed class TestAgentB : TestAgent, IHandle<TestMessage, string>
    {
        public TestAgentB(AgentId id, IAgentRuntime runtime)
            : base(id, runtime, "Test agent with handler result")
        {
        }

        public ValueTask<string> HandleAsync(TestMessage item, MessageContext messageContext)
        {
            this.ReceivedMessages.Add(item.Content);
            return ValueTask.FromResult(item.Content);
        }

        public new ValueTask<AgentId?> GetAgentAsync(AgentType agent, CancellationToken cancellationToken = default) => base.GetAgentAsync(agent, cancellationToken);
    }

    // TestAgent that implements handler for TestMessage that responds by publishing to a topic
    private sealed class TestAgentC : TestAgent, IHandle<TestMessage>
    {
        private readonly TopicId _broadcastTopic;

        public TestAgentC(AgentId id, IAgentRuntime runtime, TopicId broadcastTopic)
            : base(id, runtime, "Test agent that publishes")
        {
            this._broadcastTopic = broadcastTopic;
        }

        public async ValueTask HandleAsync(TestMessage item, MessageContext messageContext)
        {
            this.ReceivedMessages.Add(item.Content);
            await this.PublishMessageAsync(item, this._broadcastTopic, messageContext.MessageId, messageContext.CancellationToken);
        }
    }

    // TestAgent that implements handler for TestMessage that responds by messaging another agent
    private sealed class TestAgentD : TestAgent, IHandle<TestMessage>
    {
        private readonly AgentId _receiverId;

        public TestAgentD(AgentId id, IAgentRuntime runtime, AgentId receiverId)
            : base(id, runtime, "Test agent that sends")
        {
            this._receiverId = receiverId;
        }

        public async ValueTask HandleAsync(TestMessage item, MessageContext messageContext)
        {
            this.ReceivedMessages.Add(item.Content);
            await this.SendMessageAsync(item, this._receiverId, messageContext.MessageId, messageContext.CancellationToken);
        }
    }
}
