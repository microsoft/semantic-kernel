// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
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
        var args = JsonSerializer.Serialize(new Dictionary<string, object?>());
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", toolCallName, BinaryData.FromString(args));
        var openAIFunctionToolCall = new OpenAIFunctionToolCall(toolCall);

        // Act & Assert
        Assert.Equal(expectedName, openAIFunctionToolCall.FullyQualifiedName);
        Assert.Same(openAIFunctionToolCall.FullyQualifiedName, openAIFunctionToolCall.FullyQualifiedName);
    }

    [Fact]
    public void ToStringReturnsCorrectValue()
    {
        // Arrange
        var toolCall = ChatToolCall.CreateFunctionToolCall("id", "MyPlugin_MyFunction", BinaryData.FromString("{\n \"location\": \"San Diego\",\n \"max_price\": 300\n}"));
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
        Assert.Equal("test-argument", toolCall.FunctionArguments.ToString());
    }

    [Fact]
    public void TrackStreamingToolingUpdateWithNullUpdatesDoesNotThrowException()
    {
        // Arrange
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;
        IReadOnlyList<StreamingChatToolCallUpdate>? updates = [];

        StreamingChatToolCallUpdate update = ModelReaderWriter.Read<StreamingChatToolCallUpdate>(BinaryData.FromString("""{"index":0,"id":"call_id","type":"function","function":{"name":"WeatherPlugin-GetWeather","arguments":""}}"""))!;

        // Act
        var exception = Record.Exception(() =>
            OpenAIFunctionToolCall.TrackStreamingToolingUpdate(
                [
                    GetUpdateChunkFromString("""{"index":0,"id":"call_id","type":"function","function":{"name":"WeatherPlugin-GetWeather","arguments":""}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"{\n"}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":" "}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":" \""}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"address"}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"Code"}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"\":"}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":" \""}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"440"}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"100"}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"\"\n"}}"""),
                    GetUpdateChunkFromString("""{"index":0,"function":{"arguments":"}"}}"""),
                ],
                ref toolCallIdsByIndex,
                ref functionNamesByIndex,
                ref functionArgumentBuildersByIndex
            ));

        // Assert
        Assert.Equal(
            """
            {
              "addressCode": "440100"
            }
            """, functionArgumentBuildersByIndex![0].ToString());
        Assert.Null(exception);
    }

    [Fact]
    public void TrackStreamingToolingUpdateWithEmptyIdNameDoesNotThrowException()
    {
        // Arrange
        Dictionary<int, string>? toolCallIdsByIndex = null;
        Dictionary<int, string>? functionNamesByIndex = null;
        Dictionary<int, StringBuilder>? functionArgumentBuildersByIndex = null;

        // Act
        var exception = Record.Exception(() =>
            OpenAIFunctionToolCall.TrackStreamingToolingUpdate(
                [
                    GetUpdateChunkFromString("""{"function":{"name":"WeatherPlugin-GetWeather","arguments":"{\"addressCode"},"index":0,"id":"call_74f02d5863864109bae3d1","type":"function"}"""),
                    GetUpdateChunkFromString("""{"function":{"name":"","arguments":"\": \"44"},"index":0,"id":"","type":"function"}"""),
                    GetUpdateChunkFromString("""{"function":{"name":"","arguments":"0100"},"index":0,"id":"","type":"function"}"""),
                ],
                ref toolCallIdsByIndex,
                ref functionNamesByIndex,
                ref functionArgumentBuildersByIndex
            ));

        // Assert
        Assert.Null(exception);
        Assert.False(string.IsNullOrEmpty(toolCallIdsByIndex![0]));
        Assert.False(string.IsNullOrEmpty(functionNamesByIndex![0]));
    }

    private static StreamingChatToolCallUpdate GetUpdateChunkFromString(string jsonChunk)
        => ModelReaderWriter.Read<StreamingChatToolCallUpdate>(BinaryData.FromString(jsonChunk))!;
}
