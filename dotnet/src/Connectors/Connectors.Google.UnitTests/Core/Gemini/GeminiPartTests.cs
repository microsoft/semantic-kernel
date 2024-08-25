// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

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
    public void IsValidWhenFileDataIsNotNull()
    {
        // Arrange
        var sut = new GeminiPart { FileData = new() };

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
    internal void IsInvalidWhenMoreThanOnePropertyIsNotNull(GeminiPart sut)
    {
        // Act
        var result = sut.IsValid();

        // Assert
        Assert.False(result);
    }

#pragma warning disable CA1812 // Internal class that is apparently never instantiated; this class is used via reflection
    private sealed class GeminiPartTestData : TheoryData<GeminiPart>
#pragma warning restore CA1812 // Internal class that is apparently never instantiated
    {
        public GeminiPartTestData()
        {
            // Two properties
            this.Add(new() { Text = "text", FunctionCall = new() });
            this.Add(new() { Text = "text", InlineData = new() });
            this.Add(new() { Text = "text", FunctionResponse = new() });
            this.Add(new() { Text = "text", FileData = new() });
            this.Add(new() { InlineData = new(), FunctionCall = new() });
            this.Add(new() { InlineData = new(), FunctionResponse = new() });
            this.Add(new() { InlineData = new(), FileData = new() });
            this.Add(new() { FunctionCall = new(), FunctionResponse = new() });
            this.Add(new() { FunctionCall = new(), FileData = new() });
            this.Add(new() { FunctionResponse = new(), FileData = new() });

            // Three properties
            this.Add(new() { Text = "text", InlineData = new(), FunctionCall = new() });
            this.Add(new() { Text = "text", InlineData = new(), FunctionResponse = new() });
            this.Add(new() { Text = "text", InlineData = new(), FileData = new() });
            this.Add(new() { Text = "text", FunctionCall = new(), FunctionResponse = new() });
            this.Add(new() { Text = "text", FunctionCall = new(), FileData = new() });
            this.Add(new() { Text = "text", FunctionResponse = new(), FileData = new() });
            this.Add(new() { InlineData = new(), FunctionCall = new(), FunctionResponse = new() });
            this.Add(new() { InlineData = new(), FunctionCall = new(), FileData = new() });
            this.Add(new() { InlineData = new(), FunctionResponse = new(), FileData = new() });
            this.Add(new() { FunctionCall = new(), FunctionResponse = new(), FileData = new() });

            // Four properties
            this.Add(new() { Text = "text", InlineData = new(), FunctionCall = new(), FunctionResponse = new() });
            this.Add(new() { Text = "text", InlineData = new(), FunctionCall = new(), FileData = new() });
            this.Add(new() { Text = "text", InlineData = new(), FunctionResponse = new(), FileData = new() });
            this.Add(new() { Text = "text", FunctionCall = new(), FunctionResponse = new(), FileData = new() });
            this.Add(new() { InlineData = new(), FunctionCall = new(), FunctionResponse = new(), FileData = new() });

            // Five properties
            this.Add(new() { Text = "text", InlineData = new(), FunctionCall = new(), FunctionResponse = new(), FileData = new() });
        }
    }
}
