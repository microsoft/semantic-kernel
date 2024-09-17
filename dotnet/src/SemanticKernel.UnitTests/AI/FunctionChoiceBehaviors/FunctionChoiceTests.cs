// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.AI.FunctionChoiceBehaviors;

public class FunctionChoiceTests
{
    [Fact]
    public void ItShouldInitializeLabelForAutoFunctionChoice()
    {
        // Act
        var choice = FunctionChoice.Auto;

        // Assert
        Assert.Equal("auto", choice.Label);
    }

    [Fact]
    public void ItShouldInitializeLabelForRequiredFunctionChoice()
    {
        // Act
        var choice = FunctionChoice.Required;

        // Assert
        Assert.Equal("required", choice.Label);
    }

    [Fact]
    public void ItShouldInitializeLabelForNoneFunctionChoice()
    {
        // Act
        var choice = FunctionChoice.None;

        // Assert
        Assert.Equal("none", choice.Label);
    }

    [Fact]
    public void ItShouldCheckTwoChoicesAreEqual()
    {
        // Arrange
        var choice1 = FunctionChoice.Auto;
        var choice2 = FunctionChoice.Auto;

        // Act & Assert
        Assert.True(choice1 == choice2);
    }

    [Fact]
    public void ItShouldCheckTwoChoicesAreNotEqual()
    {
        // Arrange
        var choice1 = FunctionChoice.Auto;
        var choice2 = FunctionChoice.Required;

        // Act & Assert
        Assert.False(choice1 == choice2);
    }

    [Fact]
    public void ItShouldCheckChoiceIsEqualToItself()
    {
        // Arrange
        var choice = FunctionChoice.Auto;

        // Act & Assert
#pragma warning disable CS1718 // Comparison made to same variable
        Assert.True(choice == choice);
#pragma warning restore CS1718 // Comparison made to same variable
    }

    [Fact]
    public void ItShouldCheckChoiceIsNotEqualToDifferentType()
    {
        // Arrange
        var choice = FunctionChoice.Auto;

        // Act & Assert
        Assert.False(choice.Equals("auto"));
    }

    [Fact]
    public void ItShouldCheckChoiceIsNotEqualToNull()
    {
        // Arrange
        var choice = FunctionChoice.Auto;

        // Act & Assert
        Assert.False(choice.Equals(null));
    }

    [Fact]
    public void ToStringShouldReturnLabel()
    {
        // Arrange
        var choice = FunctionChoice.Auto;

        // Act
        var result = choice.ToString();

        // Assert
        Assert.Equal("auto", result);
    }
}
