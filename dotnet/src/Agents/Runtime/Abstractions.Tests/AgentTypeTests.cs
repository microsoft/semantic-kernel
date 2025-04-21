// Copyright (c) Microsoft. All rights reserved.

using System;
using Xunit;

namespace Microsoft.SemanticKernel.Agents.Runtime.Abstractions.Tests;

[Trait("Category", "Unit")]
public class AgentTypeTests
{
    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("invalid type")] // Agent type must only contain alphanumeric letters or underscores
    [InlineData("123invalidType")] // Agent type cannot start with a number
    [InlineData("invalid@type")] // Agent type must only contain alphanumeric letters or underscores
    [InlineData("invalid-type")] // Agent type cannot alphanumeric underscores.
    public void AgentIdShouldThrowArgumentExceptionWithInvalidType(string? invalidType)
    {
        // Act & Assert
        ArgumentException exception = Assert.Throws<ArgumentException>(() => new AgentType(invalidType!));
        Assert.Contains("Invalid AgentId type", exception.Message);
    }

    [Fact]
    public void ImplicitConversionFromStringTest()
    {
        // Arrange
        string agentTypeName = "TestAgent";

        // Act
        AgentType agentType = agentTypeName;

        // Assert
        Assert.Equal(agentTypeName, agentType.Name);
    }

    [Fact]
    public void ImplicitConversionToStringTest()
    {
        // Arrange
        AgentType agentType = "TestAgent";

        // Act
        string agentTypeName = agentType;

        // Assert
        Assert.Equal("TestAgent", agentTypeName);
    }

    [Fact]
    public void ExplicitConversionFromTypeTest()
    {
        // Arrange
        Type type = typeof(string);

        // Act
        AgentType agentType = (AgentType)type;

        // Assert
        Assert.Equal(type.Name, agentType.Name);
    }
}
