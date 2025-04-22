// Copyright (c) Microsoft. All rights reserved.

using System;
using FluentAssertions;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Tests;

[Trait("Category", "Unit")]
public class TypeSubscriptionTests
{
    [Fact]
    public void Constructor_WithProvidedId_ShouldSetProperties()
    {
        // Arrange
        string topicType = "testTopic";
        AgentType agentType = new("testAgent");
        string id = "custom-id";

        // Act
        TypeSubscription subscription = new(topicType, agentType, id);

        // Assert
        subscription.TopicType.Should().Be(topicType);
        subscription.AgentType.Should().Be(agentType);
        subscription.Id.Should().Be(id);
    }

    [Fact]
    public void Constructor_WithoutId_ShouldGenerateGuid()
    {
        // Arrange
        string topicType = "testTopic";
        AgentType agentType = new("testAgent");

        // Act
        TypeSubscription subscription = new(topicType, agentType);

        // Assert
        subscription.TopicType.Should().Be(topicType);
        subscription.AgentType.Should().Be(agentType);
        subscription.Id.Should().NotBeNullOrEmpty();
        Guid.TryParse(subscription.Id, out _).Should().BeTrue();
    }

    [Fact]
    public void Matches_TopicWithMatchingType_ShouldReturnTrue()
    {
        // Arrange
        string topicType = "testTopic";
        TypeSubscription subscription = new(topicType, new AgentType("testAgent"));
        TopicId topic = new(topicType, "source1");

        // Act
        bool result = subscription.Matches(topic);

        // Assert
        result.Should().BeTrue();
    }

    [Fact]
    public void Matches_TopicWithDifferentType_ShouldReturnFalse()
    {
        // Arrange
        TypeSubscription subscription = new("testTopic", new AgentType("testAgent"));
        TopicId topic = new("differentTopic", "source1");

        // Act
        bool result = subscription.Matches(topic);

        // Assert
        result.Should().BeFalse();
    }

    [Fact]
    public void MapToAgent_MatchingTopic_ShouldReturnCorrectAgentId()
    {
        // Arrange
        string topicType = "testTopic";
        string source = "source1";
        AgentType agentType = new("testAgent");
        TypeSubscription subscription = new(topicType, agentType);
        TopicId topic = new(topicType, source);

        // Act
        var agentId = subscription.MapToAgent(topic);

        // Assert
        agentId.Type.Should().Be(agentType.Name);
        agentId.Key.Should().Be(source);
    }

    [Fact]
    public void MapToAgent_NonMatchingTopic_ShouldThrowInvalidOperationException()
    {
        // Arrange
        TypeSubscription subscription = new("testTopic", new AgentType("testAgent"));
        TopicId topic = new("differentTopic", "source1");

        // Act & Assert
        Action action = () => subscription.MapToAgent(topic);
        action.Should().Throw<InvalidOperationException>()
            .WithMessage("TopicId does not match the subscription.");
    }

    [Fact]
    public void Equals_SameId_ShouldReturnTrue()
    {
        // Arrange
        string id = "custom-id";
        TypeSubscription subscription1 = new("topic1", new AgentType("agent1"), id);
        TypeSubscription subscription2 = new("topic2", new AgentType("agent2"), id);

        // Act & Assert
        subscription1.Equals((object)subscription2).Should().BeTrue();
        subscription1.Equals(subscription2 as ISubscriptionDefinition).Should().BeTrue();
    }

    [Fact]
    public void Equals_SameTypeAndAgentType_ShouldReturnTrue()
    {
        // Arrange
        string topicType = "topic1";
        AgentType agentType = new("agent1");
        TypeSubscription subscription1 = new(topicType, agentType, "id1");
        TypeSubscription subscription2 = new(topicType, agentType, "id2");

        // Act & Assert
        subscription1.Equals((object)subscription2).Should().BeTrue();
    }

    [Fact]
    public void Equals_DifferentIdAndProperties_ShouldReturnFalse()
    {
        // Arrange
        TypeSubscription subscription1 = new("topic1", new AgentType("agent1"), "id1");
        TypeSubscription subscription2 = new("topic2", new AgentType("agent2"), "id2");

        // Act & Assert
        subscription1.Equals((object)subscription2).Should().BeFalse();
        subscription1.Equals(subscription2 as ISubscriptionDefinition).Should().BeFalse();
    }

    [Fact]
    public void Equals_WithNull_ShouldReturnFalse()
    {
        // Arrange
        TypeSubscription subscription = new("topic1", new AgentType("agent1"));

        // Act & Assert
        subscription.Equals(null as object).Should().BeFalse();
        subscription.Equals(null as ISubscriptionDefinition).Should().BeFalse();
    }

    [Fact]
    public void Equals_WithDifferentType_ShouldReturnFalse()
    {
        // Arrange
        TypeSubscription subscription = new("topic1", new AgentType("agent1"));
        object differentObject = new();

        // Act & Assert
        subscription.Equals(differentObject).Should().BeFalse();
    }

    [Fact]
    public void GetHashCode_SameValues_ShouldReturnSameHashCode()
    {
        // Arrange
        string id = "custom-id";
        string topicType = "topic1";
        AgentType agentType = new("agent1");
        TypeSubscription subscription1 = new(topicType, agentType, id);
        TypeSubscription subscription2 = new(topicType, agentType, id);

        // Act & Assert
        subscription1.GetHashCode().Should().Be(subscription2.GetHashCode());
    }

    [Fact]
    public void GetHashCode_DifferentValues_ShouldReturnDifferentHashCodes()
    {
        // Arrange
        TypeSubscription subscription1 = new("topic1", new AgentType("agent1"), "id1");
        TypeSubscription subscription2 = new("topic2", new AgentType("agent2"), "id2");

        // Act & Assert
        subscription1.GetHashCode().Should().NotBe(subscription2.GetHashCode());
    }
}
