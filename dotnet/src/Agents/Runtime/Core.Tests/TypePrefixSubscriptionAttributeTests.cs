// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Tests;

[Trait("Category", "Unit")]
public class TypePrefixSubscriptionAttributeTests
{
    [Fact]
    public void Constructor_SetsTopicCorrectly()
    {
        // Arrange & Act
        TypePrefixSubscriptionAttribute attribute = new("test-topic");

        // Assert
        Assert.Equal("test-topic", attribute.Topic);
    }

    [Fact]
    public void Bind_CreatesTypeSubscription()
    {
        // Arrange
        TypePrefixSubscriptionAttribute attribute = new("test");
        AgentType agentType = new("testagent");

        // Act
        ISubscriptionDefinition subscription = attribute.Bind(agentType);

        // Assert
        Assert.NotNull(subscription);
        TypePrefixSubscription typeSubscription = Assert.IsType<TypePrefixSubscription>(subscription);
        Assert.Equal("test", typeSubscription.TopicTypePrefix);
        Assert.Equal(agentType, typeSubscription.AgentType);
    }

    [Fact]
    public void AttributeUsage_AllowsOnlyClasses()
    {
        // Arrange
        Type attributeType = typeof(TypePrefixSubscriptionAttribute);

        // Act
        AttributeUsageAttribute usageAttribute =
            (AttributeUsageAttribute)Attribute.GetCustomAttribute(
                attributeType,
                typeof(AttributeUsageAttribute))!;

        // Assert
        Assert.NotNull(usageAttribute);
        Assert.Equal(AttributeTargets.Class, usageAttribute.ValidOn);
    }
}
