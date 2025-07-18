// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using FluentAssertions;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.InProcess.Tests;

[Trait("Category", "Unit")]
public class InProcessRuntimeTests()
{
    [Fact]
    [Trait("Category", "Unit")]
    public async Task RuntimeStatusLifecycleTest()
    {
        // Arrange & Act
        await using InProcessRuntime runtime = new();

        // Assert
        Assert.False(runtime.DeliverToSelf);
        Assert.Equal(0, runtime.messageQueueCount);

        // Act
        await runtime.StopAsync(); // Already stopped
        await runtime.RunUntilIdleAsync(); // Never throws

        await runtime.StartAsync();

        // Assert
        // Invalid to start runtime that is already started
        await Assert.ThrowsAsync<InvalidOperationException>(() => runtime.StartAsync());
        Assert.Equal(0, runtime.messageQueueCount);

        // Act
        await runtime.StopAsync();

        // Assert
        Assert.Equal(0, runtime.messageQueueCount);
    }

    [Fact]
    [Trait("Category", "Unit")]
    public async Task SubscriptionRegistrationLifecycleTest()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        TestSubscription subscription = new("TestTopic", "MyAgent");

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.RemoveSubscriptionAsync(subscription.Id));

        // Arrange
        await runtime.AddSubscriptionAsync(subscription);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.AddSubscriptionAsync(subscription));

        // Act
        await runtime.RemoveSubscriptionAsync(subscription.Id);
    }

    [Fact]
    [Trait("Category", "Unit")]
    public async Task AgentRegistrationLifecycleTest()
    {
        // Arrange
        const string agentType = "MyAgent";
        const string agentDescription = "A test agent";
        List<MockAgent> agents = [];
        await using InProcessRuntime runtime = new();

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.GetAgentAsync(agentType, lazy: false));

        // Arrange
        await runtime.RegisterAgentFactoryAsync(agentType, factoryFunc);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.RegisterAgentFactoryAsync(agentType, factoryFunc));

        // Act: Lookup by type
        AgentId agentId = await runtime.GetAgentAsync(agentType, lazy: false);

        // Assert
        Assert.Single(agents);
        Assert.Single(runtime.agentInstances);

        // Act
        MockAgent agent = await runtime.TryGetUnderlyingAgentInstanceAsync<MockAgent>(agentId);

        // Assert
        Assert.Equal(agentId, agent.Id);

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () => await runtime.TryGetUnderlyingAgentInstanceAsync<WrongAgent>(agentId));

        // Act: Lookup by ID
        AgentId sameId = await runtime.GetAgentAsync(agentId, lazy: false);

        // Assert
        Assert.Equal(agentId, sameId);

        // Act: Lookup by Type
        sameId = await runtime.GetAgentAsync((AgentType)agent.Id.Type, lazy: false);

        // Assert
        Assert.Equal(agentId, sameId);

        // Act: Lookup metadata
        AgentMetadata metadata = await runtime.GetAgentMetadataAsync(agentId);

        // Assert
        Assert.Equal(agentId.Type, metadata.Type);
        Assert.Equal(agentDescription, metadata.Description);
        Assert.Equal(agentId.Key, metadata.Key);

        // Act: Access proxy
        AgentProxy proxy = await runtime.TryGetAgentProxyAsync(agentId);

        // Assert
        Assert.Equal(agentId, proxy.Id);
        Assert.Equal(metadata.Type, proxy.Metadata.Type);
        Assert.Equal(metadata.Description, proxy.Metadata.Description);
        Assert.Equal(metadata.Key, proxy.Metadata.Key);

        ValueTask<MockAgent> factoryFunc(AgentId id, IAgentRuntime runtime)
        {
            MockAgent agent = new(id, runtime, agentDescription);
            agents.Add(agent);
            return ValueTask.FromResult(agent);
        }
    }

    [Fact]
    [Trait("Category", "Unit")]
    public async Task AgentStateLifecycleTest()
    {
        // Arrange
        const string agentType = "MyAgent";
        const string testMessage = "test message";

        await using InProcessRuntime firstRuntime = new();
        await firstRuntime.RegisterAgentFactoryAsync(agentType, factoryFunc);

        // Act
        AgentId agentId = await firstRuntime.GetAgentAsync(agentType, lazy: false);

        // Assert
        Assert.Single(firstRuntime.agentInstances);

        // Arrange
        MockAgent agent = (MockAgent)firstRuntime.agentInstances[agentId];
        agent.ReceivedMessages.Add(testMessage);

        // Act
        JsonElement agentState = await firstRuntime.SaveAgentStateAsync(agentId);

        // Arrange
        await using InProcessRuntime secondRuntime = new();
        await secondRuntime.RegisterAgentFactoryAsync(agentType, factoryFunc);

        // Act
        await secondRuntime.LoadAgentStateAsync(agentId, agentState);

        // Assert
        Assert.Single(secondRuntime.agentInstances);
        MockAgent copy = (MockAgent)secondRuntime.agentInstances[agentId];
        Assert.Single(copy.ReceivedMessages);
        Assert.Equal(testMessage, copy.ReceivedMessages.Single().ToString());

        static ValueTask<MockAgent> factoryFunc(AgentId id, IAgentRuntime runtime)
        {
            MockAgent agent = new(id, runtime, "A test agent");
            return ValueTask.FromResult(agent);
        }
    }

    [Fact]
    [Trait("Category", "Unit")]
    public async Task RuntimeSendMessageTest()
    {
        // Arrange
        await using InProcessRuntime runtime = new();
        MockAgent? agent = null;
        await runtime.RegisterAgentFactoryAsync("MyAgent", (id, runtime) =>
        {
            agent = new MockAgent(id, runtime, "A test agent");
            return ValueTask.FromResult(agent);
        });

        // Act: Ensure the agent is actually created
        AgentId agentId = await runtime.GetAgentAsync("MyAgent", lazy: false);

        // Assert
        Assert.NotNull(agent);
        Assert.Empty(agent.ReceivedMessages);

        // Act: Send message
        await runtime.StartAsync();
        await runtime.SendMessageAsync("TestMessage", agent.Id);
        await runtime.RunUntilIdleAsync();

        // Assert
        Assert.Equal(0, runtime.messageQueueCount);
        Assert.Single(agent.ReceivedMessages);
    }

    // Agent will not deliver to self will success when runtime.DeliverToSelf is false (default)
    [Theory]
    [InlineData(false, 0)]
    [InlineData(true, 1)]
    [Trait("Category", "Unit")]
    public async Task RuntimeAgentPublishToSelfTest(bool selfPublish, int receiveCount)
    {
        // Arrange
        await using InProcessRuntime runtime = new()
        {
            DeliverToSelf = selfPublish
        };

        MockAgent? agent = null;
        await runtime.RegisterAgentFactoryAsync("MyAgent", (id, runtime) =>
        {
            agent = new MockAgent(id, runtime, "A test agent");
            return ValueTask.FromResult(agent);
        });

        // Assert
        runtime.agentInstances.Count.Should().Be(0, "No Agent should be registered in the runtime");

        // Act: Ensure the agent is actually created
        AgentId agentId = await runtime.GetAgentAsync("MyAgent", lazy: false);

        // Assert
        Assert.NotNull(agent);
        runtime.agentInstances.Count.Should().Be(1, "Agent should be registered in the runtime");

        const string TopicType = "TestTopic";

        // Arrange
        await runtime.AddSubscriptionAsync(new TestSubscription(TopicType, agentId.Type));

        // Act
        await runtime.StartAsync();
        await runtime.PublishMessageAsync("SelfMessage", new TopicId(TopicType), sender: agentId);
        await runtime.RunUntilIdleAsync();

        // Assert
        Assert.Equal(receiveCount, agent.ReceivedMessages.Count);
    }

    [Fact]
    [Trait("Category", "Unit")]
    public async Task RuntimeShouldSaveLoadStateCorrectlyTest()
    {
        // Arrange: Create a runtime and register an agent
        await using InProcessRuntime runtime = new();
        MockAgent? agent = null;
        await runtime.RegisterAgentFactoryAsync("MyAgent", (id, runtime) =>
        {
            agent = new MockAgent(id, runtime, "test agent");
            return ValueTask.FromResult(agent);
        });

        // Get agent ID and instantiate agent by publishing
        AgentId agentId = await runtime.GetAgentAsync("MyAgent", lazy: false);
        const string TopicType = "TestTopic";
        await runtime.AddSubscriptionAsync(new TestSubscription(TopicType, agentId.Type));

        await runtime.StartAsync();
        await runtime.PublishMessageAsync("test", new TopicId(TopicType));
        await runtime.RunUntilIdleAsync();

        // Act: Save the state
        JsonElement savedState = await runtime.SaveStateAsync();

        // Assert: Ensure the agent's state is stored as a valid JSON type
        Assert.NotNull(agent);
        savedState.TryGetProperty(agentId.ToString(), out JsonElement agentState).Should().BeTrue("Agent state should be saved");
        agentState.ValueKind.Should().Be(JsonValueKind.Array, "Agent state should be stored as a JSON array");
        agent.ReceivedMessages.Count.Should().Be(1, "Agent should be have state restored");

        // Arrange: Serialize and Deserialize the state to simulate persistence
        string json = JsonSerializer.Serialize(savedState);
        json.Should().NotBeNullOrEmpty("Serialized state should not be empty");
        IDictionary<string, JsonElement> deserializedState = JsonSerializer.Deserialize<IDictionary<string, JsonElement>>(json)
            ?? throw new InvalidOperationException("Deserialized state is unexpectedly null");
        deserializedState.Should().ContainKey(agentId.ToString());

        // Act: Start new runtime and restore the state
        agent = null;
        await using InProcessRuntime newRuntime = new();
        await newRuntime.StartAsync();
        await newRuntime.RegisterAgentFactoryAsync("MyAgent", (id, runtime) =>
        {
            agent = new MockAgent(id, runtime, "another agent");
            return ValueTask.FromResult(agent);
        });

        // Assert: Show that no agent instances exist in the new runtime
        newRuntime.agentInstances.Count.Should().Be(0, "Agent should be registered in the new runtime");

        // Act: Load the state into the new runtime and show that agent is now instantiated
        await newRuntime.LoadStateAsync(savedState);

        // Assert
        Assert.NotNull(agent);
        newRuntime.agentInstances.Count.Should().Be(1, "Agent should be registered in the new runtime");
        newRuntime.agentInstances.Should().ContainKey(agentId, "Agent should be loaded into the new runtime");
        agent.ReceivedMessages.Count.Should().Be(1, "Agent should be have state restored");
    }

    private sealed class TextMessage
    {
        public string Source { get; set; } = string.Empty;
        public string Content { get; set; } = string.Empty;
    }

    private sealed class WrongAgent : IAgent, IHostableAgent
    {
        public AgentId Id => throw new NotImplementedException();

        public AgentMetadata Metadata => throw new NotImplementedException();

        public ValueTask CloseAsync() => ValueTask.CompletedTask;

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
