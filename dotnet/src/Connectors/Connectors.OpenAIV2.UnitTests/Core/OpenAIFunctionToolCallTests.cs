// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text;
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
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", toolCallName, string.Empty);
        var openAIFunctionToolCall = new OpenAIFunctionToolCall(toolCall);

        // Act & Assert
        Assert.Equal(expectedName, openAIFunctionToolCall.FullyQualifiedName);
        Assert.Same(openAIFunctionToolCall.FullyQualifiedName, openAIFunctionToolCall.FullyQualifiedName);
    }

    [Fact]
    public void ToStringReturnsCorrectValue()
    {
        // Arrange
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", "{\n \"location\": \"San Diego\",\n \"max_price\": 300\n}");
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
        Assert.Equal("test-argument", toolCall.FunctionArguments);
    }
}
