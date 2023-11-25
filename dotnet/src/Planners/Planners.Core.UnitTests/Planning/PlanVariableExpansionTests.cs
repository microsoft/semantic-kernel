// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Planning;
using Xunit;

namespace SemanticKernel.UnitTests.Planning;

public sealed class PlanVariableExpansionTests
{
    [Fact]
    public void ExpandFromVariablesWithNoVariablesReturnsInput()
    {
        // Arrange
        var input = "Hello world!";
        var variables = new ContextVariables();
        var plan = new Plan("This is my goal");

        // Act
        var result = plan.ExpandFromVariables(variables, input);

        // Assert
        Assert.Equal(input, result);
    }

    [Theory]
    [InlineData("Hello $name! $greeting", "Hello Bob! How are you?", "name", "Bob", "greeting", "How are you?")]
    [InlineData("$SOMETHING_ELSE;$SOMETHING_ELSE2", "The string;Another string", "SOMETHING_ELSE", "The string", "SOMETHING_ELSE2", "Another string")]
    [InlineData("[$FirstName,$LastName,$Age]", "[John,Doe,35]", "FirstName", "John", "LastName", "Doe", "Age", "35")]
    [InlineData("$Category ($Count)", "Fruits (3)", "Category", "Fruits", "Count", "3")]
    [InlineData("$Animal eats $Food", "Dog eats Bones", "Animal", "Dog", "Food", "Bones")]
    [InlineData("$Country is in $Continent", "Canada is in North America", "Country", "Canada", "Continent", "North America")]
    [InlineData("Hello $name", "Hello world", "name", "world")]
    [InlineData("$VAR1 $VAR2", "value1 value2", "VAR1", "value1", "VAR2", "value2")]
    [InlineData("$A-$A-$A", "x-x-x", "A", "x")]
    [InlineData("$A$B$A", "aba", "A", "a", "B", "b")]
    [InlineData("$ABC", "$ABC", "A", "", "B", "", "C", "")]
    [InlineData("$NO_VAR", "$NO_VAR", "A", "a", "B", "b", "C", "c")]
    [InlineData("$name$invalid_name", "world$invalid_name", "name", "world")]
    public void ExpandFromVariablesWithVariablesReturnsExpandedString(string input, string expected, params string[] variables)
    {
        // Arrange
        var contextVariables = new ContextVariables();
        for (var i = 0; i < variables.Length; i += 2)
        {
            contextVariables.Set(variables[i], variables[i + 1]);
        }

        var plan = new Plan("This is my goal");

        // Act
        var result = plan.ExpandFromVariables(contextVariables, input);

        // Assert
        Assert.Equal(expected, result);
    }
}
