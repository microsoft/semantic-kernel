// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Connectors.Google;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

/// <summary>
/// Unit tests for <see cref="GeminiFunctionToolCall"/> class.
/// </summary>
public sealed class GeminiFunctionToolCallTests
{
    [Theory]
    [InlineData("MyFunction")]
    [InlineData("MyPlugin_MyFunction")]
    public void FullyQualifiedNameReturnsValidName(string toolCallName)
    {
        // Arrange
        var toolCallPart = new GeminiPart.FunctionCallPart { FunctionName = toolCallName };
        var functionToolCall = new GeminiFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Equal(toolCallName, functionToolCall.FullyQualifiedName);
    }

    [Fact]
    public void ArgumentsReturnsCorrectValue()
    {
        // Arrange
        var toolCallPart = new GeminiPart.FunctionCallPart
        {
            FunctionName = "MyPlugin_MyFunction",
            Arguments = new JsonObject
            {
                { "location", "San Diego" },
                { "max_price", 300 }
            }
        };
        var functionToolCall = new GeminiFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.NotNull(functionToolCall.Arguments);
        Assert.Equal(2, functionToolCall.Arguments.Count);
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
            Arguments = new JsonObject
            {
                { "location", "San Diego" },
                { "max_price", 300 }
            }
        };
        var functionToolCall = new GeminiFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Equal("MyPlugin_MyFunction(location:San Diego, max_price:300)", functionToolCall.ToString());
    }

    [Fact]
    public void ThoughtSignatureIsNullWhenCreatedFromFunctionCallPart()
    {
        // Arrange - Using the FunctionCallPart constructor (no ThoughtSignature)
        var toolCallPart = new GeminiPart.FunctionCallPart { FunctionName = "MyFunction" };
        var functionToolCall = new GeminiFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Null(functionToolCall.ThoughtSignature);
    }

    [Fact]
    public void ThoughtSignatureIsCapturedWhenCreatedFromGeminiPart()
    {
        // Arrange - Using the GeminiPart constructor (with ThoughtSignature)
        var part = new GeminiPart
        {
            FunctionCall = new GeminiPart.FunctionCallPart { FunctionName = "MyFunction" },
            ThoughtSignature = "test-thought-signature-123"
        };
        var functionToolCall = new GeminiFunctionToolCall(part);

        // Act & Assert
        Assert.Equal("test-thought-signature-123", functionToolCall.ThoughtSignature);
    }

    [Fact]
    public void ThoughtSignatureIsNullWhenGeminiPartHasNoSignature()
    {
        // Arrange
        var part = new GeminiPart
        {
            FunctionCall = new GeminiPart.FunctionCallPart { FunctionName = "MyFunction" },
            ThoughtSignature = null
        };
        var functionToolCall = new GeminiFunctionToolCall(part);

        // Act & Assert
        Assert.Null(functionToolCall.ThoughtSignature);
    }

    [Fact]
    public void ArgumentsArePreservedWhenCreatedFromGeminiPart()
    {
        // Arrange
        var part = new GeminiPart
        {
            FunctionCall = new GeminiPart.FunctionCallPart
            {
                FunctionName = "MyPlugin_MyFunction",
                Arguments = new JsonObject
                {
                    { "location", "San Diego" },
                    { "max_price", 300 }
                }
            },
            ThoughtSignature = "signature-abc"
        };
        var functionToolCall = new GeminiFunctionToolCall(part);

        // Act & Assert
        Assert.NotNull(functionToolCall.Arguments);
        Assert.Equal(2, functionToolCall.Arguments.Count);
        Assert.Equal("San Diego", functionToolCall.Arguments["location"]!.ToString());
        Assert.Equal("signature-abc", functionToolCall.ThoughtSignature);
    }
}
