// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using Microsoft.SemanticKernel.Connectors.GoogleVertexAI;
using Xunit;

namespace SemanticKernel.Connectors.GoogleVertexAI.UnitTests.Core.Gemini;

/// <summary>
/// Unit tests for <see cref="GeminiFunctionToolCall"/> class.
/// </summary>
public sealed class GeminiFunctionToolCallTests
{
    [Theory]
    [InlineData("MyFunction", "MyFunction")]
    [InlineData("MyPlugin_MyFunction", "MyPlugin_MyFunction")]
    public void FullyQualifiedNameReturnsValidName(string toolCallName, string expectedName)
    {
        // Arrange
        var toolCallPart = new GeminiPart.FunctionCallPart { FunctionName = toolCallName };
        var functionToolCall = new GeminiFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Equal(expectedName, functionToolCall.FullyQualifiedName);
    }

    [Fact]
    public void ArgumentsReturnsCorrectValue()
    {
        // Arrange
        var toolCallPart = new GeminiPart.FunctionCallPart
        {
            FunctionName = "MyPlugin_MyFunction",
            Arguments = new BinaryData(
                """
                {
                 "location": "San Diego",
                 "max_price": 300
                }
                """)
        };
        var functionToolCall = new GeminiFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Equal(2, functionToolCall.Arguments!.Count);
        Assert.Equal("San Diego", functionToolCall.Arguments["location"]!.ToString());
        Assert.Equal(300,
            Convert.ToInt32(functionToolCall.Arguments["max_price"]!.ToString(), new NumberFormatInfo()));
    }

    [Fact]
    public void ToStringReturnsCorrectValue()
    {
        // Arrange
        var toolCallPart = new GeminiPart.FunctionCallPart
        {
            FunctionName = "MyPlugin_MyFunction",
            Arguments = new BinaryData(
                """
                {
                 "location": "San Diego",
                 "max_price": 300
                }
                """)
        };
        var functionToolCall = new GeminiFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Equal("MyPlugin_MyFunction(location:San Diego, max_price:300)", functionToolCall.ToString());
    }
}
