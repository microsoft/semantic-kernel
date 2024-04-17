// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel.Connectors.Anthropic;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Models;

/// <summary>
/// Unit tests for <see cref="AnthropicFunctionToolCall"/> class.
/// </summary>
public sealed class AnthropicFunctionToolCallTests
{
    [Theory]
    [InlineData("MyFunction")]
    [InlineData("MyPlugin_MyFunction")]
    public void FullyQualifiedNameReturnsValidName(string toolCallName)
    {
        // Arrange
        var toolCallPart = new AnthropicToolCallContent { FunctionName = toolCallName };
        var functionToolCall = new AnthropicFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Equal(toolCallName, functionToolCall.FullyQualifiedName);
    }

    [Fact]
    public void ArgumentsReturnsCorrectValue()
    {
        // Arrange
        var toolCallPart = new AnthropicToolCallContent
        {
            FunctionName = "MyPlugin_MyFunction",
            Arguments = new JsonObject
            {
                { "location", "San Diego" },
                { "max_price", 300 }
            }
        };
        var functionToolCall = new AnthropicFunctionToolCall(toolCallPart);

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
        var toolCallPart = new AnthropicToolCallContent
        {
            FunctionName = "MyPlugin_MyFunction",
            Arguments = new JsonObject
            {
                { "location", "San Diego" },
                { "max_price", 300 }
            }
        };
        var functionToolCall = new AnthropicFunctionToolCall(toolCallPart);

        // Act & Assert
        Assert.Equal("MyPlugin_MyFunction(location:San Diego, max_price:300)", functionToolCall.ToString());
    }
}
