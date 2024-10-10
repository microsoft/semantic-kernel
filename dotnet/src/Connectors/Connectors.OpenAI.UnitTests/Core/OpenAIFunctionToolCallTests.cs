// Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using System.Collections.Generic;
using System.Text;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.Collections.Generic;
using System.Text;
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
using System.Collections.Generic;
using System.Text;
=======
>>>>>>> Stashed changes
using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Connectors.OpenAI;
using OpenAI.Chat;
using Xunit;

namespace SemanticKernel.Connectors.OpenAI.UnitTests.Core;

/// <summary>
/// Unit tests for <see cref="OpenAIFunctionToolCall"/> class.
/// </summary>
public sealed class OpenAIFunctionToolCallTests
{
    [Theory]
    [InlineData("MyFunction", "MyFunction")]
    [InlineData("MyPlugin_MyFunction", "MyPlugin_MyFunction")]
    public void FullyQualifiedNameReturnsValidName(string toolCallName, string expectedName)
    {
        // Arrange
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", toolCallName, string.Empty);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", toolCallName, string.Empty);
=======
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", toolCallName, BinaryData.FromString(args));
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", toolCallName, BinaryData.FromString(args));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        var openAIFunctionToolCall = new OpenAIFunctionToolCall(toolCall);

        // Act & Assert
        Assert.Equal(expectedName, openAIFunctionToolCall.FullyQualifiedName);
        Assert.Same(openAIFunctionToolCall.FullyQualifiedName, openAIFunctionToolCall.FullyQualifiedName);
    }

    [Fact]
    public void ToStringReturnsCorrectValue()
    {
        // Arrange
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", "{\n \"location\": \"San Diego\",\n \"max_price\": 300\n}");
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", "{\n \"location\": \"San Diego\",\n \"max_price\": 300\n}");
=======
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", BinaryData.FromString("{\n \"location\": \"San Diego\",\n \"max_price\": 300\n}"));
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", BinaryData.FromString("{\n \"location\": \"San Diego\",\n \"max_price\": 300\n}"));
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        var openAIFunctionToolCall = new OpenAIFunctionToolCall(toolCall);

        // Act & Assert
        Assert.Equal("MyPlugin_MyFunction(location:San Diego, max_price:300)", openAIFunctionToolCall.ToString());
    }

    [Fact]
    public void ConvertToolCallUpdatesWithEmptyIndexesReturnsEmptyToolCalls()
    {
        // Arrange
        var toolCallIdsByIndex = new Dictionary<int, string>();
        var functionNamesByIndex = new Dictionary<int, string>();
        var functionArgumentBuildersByIndex = new Dictionary<int, StringBuilder>();

        // Act
        var toolCalls = OpenAIFunctionToolCall.ConvertToolCallUpdatesToFunctionToolCalls(
            ref toolCallIdsByIndex,
            ref functionNamesByIndex,
            ref functionArgumentBuildersByIndex);

        // Assert
        Assert.Empty(toolCalls);
    }

    [Fact]
    public void ConvertToolCallUpdatesWithNotEmptyIndexesReturnsNotEmptyToolCalls()
    {
        // Arrange
        var toolCallIdsByIndex = new Dictionary<int, string> { { 3, "test-id" } };
        var functionNamesByIndex = new Dictionary<int, string> { { 3, "test-function" } };
        var functionArgumentBuildersByIndex = new Dictionary<int, StringBuilder> { { 3, new("test-argument") } };

        // Act
        var toolCalls = OpenAIFunctionToolCall.ConvertToolCallUpdatesToFunctionToolCalls(
            ref toolCallIdsByIndex,
            ref functionNamesByIndex,
            ref functionArgumentBuildersByIndex);

        // Assert
        Assert.Single(toolCalls);

        var toolCall = toolCalls[0];

        Assert.Equal("test-id", toolCall.Id);
        Assert.Equal("test-function", toolCall.FunctionName);
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        Assert.Equal("test-argument", toolCall.FunctionArguments);
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
        Assert.Equal("test-argument", toolCall.FunctionArguments);
=======
        Assert.Equal("test-argument", toolCall.FunctionArguments.ToString());
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        Assert.Equal("test-argument", toolCall.FunctionArguments.ToString());
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
    }
}
