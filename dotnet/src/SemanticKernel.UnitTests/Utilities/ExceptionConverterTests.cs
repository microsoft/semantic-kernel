// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Nodes;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Text;
using Xunit;

namespace SemanticKernel.UnitTests.Utilities;

public class ExceptionJsonConverterTests
{
    private readonly JsonSerializerOptions _options;
    private readonly Exception? _exception;

    public ExceptionJsonConverterTests()
    {
        this._options = new JsonSerializerOptions();
#pragma warning disable CA1031 // Do not catch general exception types
        try
        {
            JsonSerializer.Deserialize<object>("invalid_json");
        }
        catch (Exception ex)
        {
            this._exception = ex;
        }
#pragma warning restore CA1031 // Do not catch general exception types

        this._options.Converters.Add(new ExceptionJsonConverter());
    }

    [Fact]
    public void ItShouldSerializesExceptionWithInnerExceptionCorrectly()
    {
        // Act
        var json = JsonSerializer.Serialize(this._exception, this._options);

        // Assert
        var jsonElement = JsonSerializer.Deserialize<JsonElement>(json);

        Assert.Equal("System.Text.Json.JsonException", jsonElement.GetProperty("className").GetString());
        Assert.Equal(this._exception!.Message, jsonElement.GetProperty("message").GetString());
        Assert.True(jsonElement.GetProperty("innerException").ValueKind == JsonValueKind.Object);
        Assert.Equal(this._exception.StackTrace, jsonElement.GetProperty("stackTraceString").GetString());

        var innerExceptionElement = jsonElement.GetProperty("innerException");
        Assert.Equal("System.Text.Json.JsonReaderException", innerExceptionElement.GetProperty("className").GetString());
        Assert.Equal(this._exception.InnerException!.Message, innerExceptionElement.GetProperty("message").GetString());
        Assert.Equal(this._exception.InnerException!.StackTrace, innerExceptionElement.GetProperty("stackTraceString").GetString());
    }

    [Fact]
    public void ItShouldSerializesExceptionWithNoInnerExceptionCorrectly()
    {
        // Act
        InvalidOperationException? exception = null;

        try
        {
            throw new InvalidOperationException("Test exception");
        }
        catch (InvalidOperationException ex)
        {
            exception = ex;
        }

        var json = JsonSerializer.Serialize(exception, this._options);

        // Assert
        var jsonElement = JsonSerializer.Deserialize<JsonElement>(json);

        Assert.Equal("System.InvalidOperationException", jsonElement.GetProperty("className").GetString());
        Assert.Equal(exception!.Message, jsonElement.GetProperty("message").GetString());
        Assert.False(jsonElement.TryGetProperty("innerException", out var _));
        Assert.Equal(exception.StackTrace, jsonElement.GetProperty("stackTraceString").GetString());
    }

    [Fact]
    public void ItShouldSerializeChatHistoryWithFunctionCallContentAndFunctionResultContent()
    {
        var chatMessageContent = new ChatMessageContent(AuthorRole.User, "Test message");
        chatMessageContent.Items.Add(new FunctionCallContent("FunctionName", "PluginName", "CallId") { Exception = this._exception });
        chatMessageContent.Items.Add(new FunctionResultContent("FunctionName", "PluginName", "CallId", this._exception));

        var chatHistory = new ChatHistory
        {
            chatMessageContent
        };

        this._options.Converters.Add(new ExceptionJsonConverter());

        // Act
        var json = JsonSerializer.Serialize(chatHistory, this._options);

        // Assert
        var jsonArray = JsonSerializer.Deserialize<JsonArray>(json)!;

        var functionCallElement = jsonArray[0]?["Items"]?[1];
        Assert.Equal("System.Text.Json.JsonException", functionCallElement?["Exception"]?["className"]?.ToString());
        Assert.Equal(this._exception!.Message, functionCallElement?["Exception"]?["message"]?.ToString());

        var functionResultElement = jsonArray[0]?["Items"]?[2];
        Assert.Equal("System.Text.Json.JsonException", functionResultElement?["Result"]?["className"]?.ToString());
        Assert.Equal(this._exception!.Message, functionResultElement?["Result"]?["message"]?.ToString());
    }
}
