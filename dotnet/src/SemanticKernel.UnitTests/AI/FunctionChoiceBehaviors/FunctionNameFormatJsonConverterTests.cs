// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.AI.FunctionChoiceBehaviors;
public class FunctionNameFormatJsonConverterTests
{
    [Fact]
    public void ItShouldDeserializeAutoFunctionChoiceBehavior()
    {
        // Arrange
        var json = """
            {
                "type": "auto",
                "functions": ["p1.f1"]
            }
            """;

        // Act
        var behavior = JsonSerializer.Deserialize<AutoFunctionChoiceBehavior>(json);

        // Assert
        Assert.NotNull(behavior?.Functions);
        Assert.Single(behavior.Functions);
        Assert.Equal("p1.f1", behavior.Functions.Single());
    }

    [Fact]
    public void ItShouldDeserializeRequiredFunctionChoiceBehavior()
    {
        // Arrange
        var json = """
            {
                "type": "required",
                "functions": ["p1.f1"]
            }
            """;

        // Act
        var behavior = JsonSerializer.Deserialize<RequiredFunctionChoiceBehavior>(json);

        // Assert
        Assert.NotNull(behavior?.Functions);
        Assert.Single(behavior.Functions);
        Assert.Equal("p1.f1", behavior.Functions.Single());
    }

    [Fact]
    public void ItShouldDeserializeNoneFunctionChoiceBehavior()
    {
        // Arrange
        var json = """
            {
                "type": "none",
                "functions": ["p1.f1"]
            }
            """;

        // Act
        var behavior = JsonSerializer.Deserialize<NoneFunctionChoiceBehavior>(json);

        // Assert
        Assert.NotNull(behavior?.Functions);
        Assert.Single(behavior.Functions);
        Assert.Equal("p1.f1", behavior.Functions.Single());
    }
}
