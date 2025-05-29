// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Core.Tests;

[Trait("Category", "Unit")]
public class TypeSubscriptionAttributeTests
{
    [Fact]
    public void Constructor_SetsTopicCorrectly()
    {
        // Arrange & Act
        TypeSubscriptionAttribute attribute = new("test-topic");

        // Assert
        Assert.Equal("test-topic", attribute.Topic);
    }

    [Fact]
    public void Bind_CreatesTypeSubscription()
    {
        // Arrange
        TypeSubscriptionAttribute attribute = new("test-topic");
        AgentType agentType = new("testagent");

        // Act
        ISubscriptionDefinition subscription = attribute.Bind(agentType);

        // Assert
        Assert.NotNull(subscription);
        TypeSubscription typeSubscription = Assert.IsType<TypeSubscription>(subscription);
        Assert.Equal("test-topic", typeSubscription.TopicType);
        Assert.Equal(agentType, typeSubscription.AgentType);
    }

    [Fact]
    public void AttributeUsage_AllowsOnlyClasses()
    {
        // Arrange
        Type attributeType = typeof(TypeSubscriptionAttribute);

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
