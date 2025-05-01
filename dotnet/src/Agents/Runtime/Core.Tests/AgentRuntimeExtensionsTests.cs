// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.SemanticKernel.Agents.Runtime.InProcess;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Tests;

[Trait("Category", "Unit")]
public class AgentRuntimeExtensionsTests
{
    private const string TestTopic1 = "test.1.topic";
    private const string TestTopic2 = "test.2.topic";
    private const string TestTopicPrefix = "test.2";

    [Fact]
    public async Task RegisterAgentTypeWithStringAsync_WithBaseAgent()
    {
        // Arrange
        string agentTypeName = nameof(TestAgent);
        Guid value = Guid.NewGuid();
        ServiceProvider serviceProvider = new ServiceCollection().BuildServiceProvider();

        await using InProcessRuntime runtime = new();

        // Act
        AgentType registeredType = await runtime.RegisterAgentTypeAsync<TestAgent>(agentTypeName, serviceProvider, [value]);
        AgentId registeredId = await runtime.GetAgentAsync(agentTypeName, lazy: false);

        // Assert
        Assert.Equal(agentTypeName, registeredType.Name);
        Assert.Equal(agentTypeName, registeredId.Type);

        // Act
        TestAgent agent = await runtime.TryGetUnderlyingAgentInstanceAsync<TestAgent>(registeredId);

        // Assert
        Assert.NotNull(agent);
        Assert.Equal(agentTypeName, agent.Id.Type);
        TestAgent testAgent = Assert.IsType<TestAgent>(agent);
        Assert.Equal(value, testAgent.Value);
    }

    [Fact]
    public async Task RegisterAgentTypeWithStringAsync_NotWithBaseAgent()
    {
        // Arrange
        string agentTypeName = nameof(NotBaseAgent);
        ServiceProvider serviceProvider = new ServiceCollection().BuildServiceProvider();

        await using InProcessRuntime runtime = new();

        // Act
        AgentType registeredType = await runtime.RegisterAgentTypeAsync(agentTypeName, typeof(NotBaseAgent), serviceProvider);

        // Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.GetAgentAsync(agentTypeName, lazy: false));
    }

    [Fact]
    public async Task RegisterImplicitAgentSubscriptionsAsync()
    {
        // Arrange
        string agentTypeName = nameof(TestAgent);
        TopicId topic1 = new(TestTopic1);
        TopicId topic2 = new(TestTopic2);

        ServiceProvider serviceProvider = new ServiceCollection().BuildServiceProvider();
        await using InProcessRuntime runtime = new();

        // Act
        AgentType registeredType = await runtime.RegisterAgentTypeAsync<TestAgent>(agentTypeName, serviceProvider, [Guid.Empty]);
        await runtime.RegisterImplicitAgentSubscriptionsAsync<TestAgent>(agentTypeName);

        // Arrange
        await runtime.StartAsync();

        try
        {
            // Act - publish messages to each topic
            string messageText1 = "Test message #1";
            string messageText2 = "Test message #1";
            await runtime.PublishMessageAsync(messageText1, topic1);
            await runtime.PublishMessageAsync(messageText2, topic2);

            // Get agent and verify it received messages
            AgentId registeredId = await runtime.GetAgentAsync(agentTypeName, lazy: false);
            TestAgent agent = await runtime.TryGetUnderlyingAgentInstanceAsync<TestAgent>(registeredId);

            // Assert
            Assert.NotNull(agent);
            Assert.Equal(2, agent.ReceivedMessages.Count);
            Assert.Contains(messageText1, agent.ReceivedMessages);
            Assert.Contains(messageText2, agent.ReceivedMessages);
        }
        finally
        {
            // Arrange
            await runtime.StopAsync();
        }
    }

    [TypeSubscription(TestTopic1)]
    [TypePrefixSubscription(TestTopicPrefix)]
    private sealed class TestAgent : BaseAgent, IHandle<string>
    {
        public List<string> ReceivedMessages { get; } = [];

        public TestAgent(AgentId id, IAgentRuntime runtime, Guid value)
            : base(id, runtime, "Test Subscribing Agent", null)
        {
            this.Value = value;
        }

        public Guid Value { get; }

        public ValueTask HandleAsync(string item, MessageContext messageContext)
        {
            this.ReceivedMessages.Add(item);

            return ValueTask.CompletedTask;
        }
    }

    private sealed class NotBaseAgent : IHostableAgent
    {
        public AgentId Id => throw new NotImplementedException();

        public AgentMetadata Metadata => throw new NotImplementedException();

        public ValueTask CloseAsync()
        {
            throw new NotImplementedException();
        }

        public ValueTask LoadStateAsync(JsonElement state)
        {
            throw new NotImplementedException();
        }

        public ValueTask<object?> OnMessageAsync(object message, MessageContext messageContext)
        {
            throw new NotImplementedException();
        }

        public ValueTask<JsonElement> SaveStateAsync()
        {
            throw new NotImplementedException();
        }
    }
}
