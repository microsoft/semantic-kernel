#region HEADER

// Copyright (c) Microsoft. All rights reserved.

#endregion

using Microsoft.SemanticKernel.Connectors.GoogleVertexAI.Core.Gemini;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini;

public sealed class GeminiPartTests
{
    [Fact]
    public void IsValidWhenTextIsNotNull()
    {
        // Arrange
        var sut = new GeminiPart { Text = "text" };

        // Act
        var result = sut.IsValid();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void IsValidWhenInlineDataIsNotNull()
    {
        // Arrange
        var sut = new GeminiPart { InlineData = new() };

        // Act
        var result = sut.IsValid();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void IsValidWhenFunctionCallIsNotNull()
    {
        // Arrange
        var sut = new GeminiPart { FunctionCall = new() };

        // Act
        var result = sut.IsValid();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void IsValidWhenFunctionResponseIsNotNull()
    {
        // Arrange
        var sut = new GeminiPart { FunctionResponse = new() };

        // Act
        var result = sut.IsValid();

        // Assert
        Assert.True(result);
    }

    [Fact]
    public void IsInvalidWhenAllPropertiesAreNull()
    {
        // Arrange
        var sut = new GeminiPart();

        // Act
        var result = sut.IsValid();

        // Assert
        Assert.False(result);
    }

    [Theory]
    [ClassData(typeof(GeminiPartTestData))]
    public void IsInvalidWhenMoreThanOnePropertyIsNotNull(GeminiPart sut)
    {
        // Act
        var result = sut.IsValid();

        // Assert
        Assert.False(result);
    }

    private sealed class GeminiPartTestData : TheoryData<GeminiPart>
    {
        public GeminiPartTestData()
        {
            // Two properties
            this.Add(new() { Text = "text", FunctionCall = new() });
            this.Add(new() { Text = "text", InlineData = new() });
            this.Add(new() { Text = "text", FunctionResponse = new() });
            this.Add(new() { InlineData = new(), FunctionCall = new() });
            this.Add(new() { InlineData = new(), FunctionResponse = new() });
            this.Add(new() { FunctionCall = new(), FunctionResponse = new() });
            // Three properties
            this.Add(new() { Text = "text", InlineData = new(), FunctionCall = new() });
            this.Add(new() { Text = "text", InlineData = new(), FunctionResponse = new() });
            this.Add(new() { Text = "text", FunctionCall = new(), FunctionResponse = new() });
            this.Add(new() { InlineData = new(), FunctionCall = new(), FunctionResponse = new() });
            // Four properties
            this.Add(new() { Text = "text", InlineData = new(), FunctionCall = new(), FunctionResponse = new() });
        }
    }
}
