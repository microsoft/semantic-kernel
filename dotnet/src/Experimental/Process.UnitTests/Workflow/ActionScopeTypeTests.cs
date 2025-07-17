// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Process.Workflows;
using Xunit;
using Xunit.Abstractions;

namespace Microsoft.SemanticKernel.Process.UnitTests.Workflows;

public sealed class ActionScopeTypeTests(ITestOutputHelper output) : WorkflowTest(output)
{
    [Fact]
    public void VerifyStaticInstances()
    {
        // Arrange & Act & Assert
        Assert.Equal(nameof(ActionScopeType.Env), ActionScopeType.Env.Name);
        Assert.Equal(nameof(ActionScopeType.Topic), ActionScopeType.Topic.Name);
        Assert.Equal(nameof(ActionScopeType.Global), ActionScopeType.Global.Name);
        Assert.Equal(nameof(ActionScopeType.System), ActionScopeType.System.Name);
    }

    [Theory]
    [InlineData(nameof(ActionScopeType.Env))]
    [InlineData(nameof(ActionScopeType.Topic))]
    [InlineData(nameof(ActionScopeType.Global))]
    [InlineData(nameof(ActionScopeType.System))]
    public void ParseValidScopeNames(string scopeName)
    {
        // Arrange & Act
        ActionScopeType result = ActionScopeType.Parse(scopeName);

        // Assert
        Assert.Equal(scopeName, result.Name);
    }

    [Fact]
    public void ParseNullInput()
    {
        // Arrange & Act & Assert
        InvalidScopeException exception = Assert.Throws<InvalidScopeException>(() => ActionScopeType.Parse(null));
        Assert.Equal("Undefined action scope type.", exception.Message);
    }

    [Fact]
    public void ParseInvalidScopeName()
    {
        // Arrange
        string invalidScope = "InvalidScope";

        // Act & Assert
        InvalidScopeException exception = Assert.Throws<InvalidScopeException>(() => ActionScopeType.Parse(invalidScope));
        Assert.Equal($"Unknown action scope type: {invalidScope}.", exception.Message);
    }

    [Fact]
    public void ToStringReturnsName()
    {
        // Arrange
        ActionScopeType scope = ActionScopeType.Env;

        // Act
        string result = scope.ToString();

        // Assert
        Assert.Equal(nameof(ActionScopeType.Env), result);
    }

    [Fact]
    public void VerifyGetHashCode()
    {
        // Arrange
        ActionScopeType scope = ActionScopeType.Topic;
        int expectedHashCode = "Topic".GetHashCode();

        // Act
        int result = scope.GetHashCode();

        // Assert
        Assert.Equal(expectedHashCode, result);
    }

    [Fact]
    public void VerifyEqualsWithSameInstance()
    {
        // Arrange
        ActionScopeType scope = ActionScopeType.Global;

        // Act
        bool result = scope.Equals(scope);

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void VerifyEqualsWithName()
    {
        // Arrange
        ActionScopeType scope = ActionScopeType.System;

        // Act
        bool result = scope.Equals(nameof(ActionScopeType.System));

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void VerifyInequalityWithName()
    {
        // Arrange
        ActionScopeType scope = ActionScopeType.Env;

        // Act
        bool result = scope.Equals("DifferentName");

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void VerifyInequalityWithNull()
    {
        // Arrange
        ActionScopeType scope = ActionScopeType.Topic;

        // Act
        bool result = scope.Equals(null);

        // Assert
        Assert.False(result);
    }

    [Fact]
    public void VerifyInequalityWithOtherType()
    {
        // Arrange
        ActionScopeType scope = ActionScopeType.Global;
        int differentTypeObject = 42;

        // Act
        bool result = scope.Equals(differentTypeObject);

        // Assert
        Assert.False(result);
    }
}
