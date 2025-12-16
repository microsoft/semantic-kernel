// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Core;

/// <summary>
/// Unit tests for AnthropicClientCore converter methods.
/// </summary>
public sealed class AnthropicClientCoreConvertersTests
{
    #region ConvertChatHistoryToAnthropicMessages Tests

    [Fact]
    public void ConvertChatHistorySkipsSystemMessages()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddSystemMessage("You are a helpful assistant.");
        chatHistory.AddUserMessage("Hello");

        // Act
        var result = AnthropicClientCore.ConvertChatHistoryToAnthropicMessages(chatHistory);

        // Assert
        Assert.Single(result);
        Assert.Equal(global::Anthropic.Models.Messages.Role.User, result[0].Role.Value());
    }

    [Fact]
    public void ConvertChatHistoryConvertsMultiTurnConversation()
    {
        // Arrange
        var chatHistory = new ChatHistory();
        chatHistory.AddUserMessage("Hello");
        chatHistory.AddAssistantMessage("Hi there!");
        chatHistory.AddUserMessage("How are you?");

        // Act
        var result = AnthropicClientCore.ConvertChatHistoryToAnthropicMessages(chatHistory);

        // Assert
        Assert.Equal(3, result.Count);
        Assert.Equal(global::Anthropic.Models.Messages.Role.User, result[0].Role.Value());
        Assert.Equal(global::Anthropic.Models.Messages.Role.Assistant, result[1].Role.Value());
        Assert.Equal(global::Anthropic.Models.Messages.Role.User, result[2].Role.Value());
    }

    #endregion

    #region MapStopReasonToFinishReason Tests

    [Theory]
    [InlineData("EndTurn", "stop")]
    [InlineData("MaxTokens", "length")]
    [InlineData("ToolUse", "tool_calls")]
    [InlineData("StopSequence", "stop")]
    public void MapStopReasonToFinishReasonMapsCorrectly(string stopReasonString, string expectedFinishReason)
    {
        // Arrange
        var stopReason = Enum.Parse<global::Anthropic.Models.Messages.StopReason>(stopReasonString);
        // Convert to ApiEnum using implicit operator
        global::Anthropic.Core.ApiEnum<string, global::Anthropic.Models.Messages.StopReason> apiEnum = stopReason;

        // Act
        var result = AnthropicClientCore.MapStopReasonToFinishReason(apiEnum);

        // Assert
        Assert.Equal(expectedFinishReason, result);
    }

    [Fact]
    public void MapStopReasonToFinishReasonReturnsNullForNull()
    {
        // Act
        global::Anthropic.Core.ApiEnum<string, global::Anthropic.Models.Messages.StopReason>? nullEnum = null;
        var result = AnthropicClientCore.MapStopReasonToFinishReason(nullEnum);

        // Assert
        Assert.Null(result);
    }

    #endregion

    #region GetJsonSchemaType Tests

    [Theory]
    [InlineData(typeof(bool), "boolean")]
    [InlineData(typeof(int), "integer")]
    [InlineData(typeof(long), "integer")]
    [InlineData(typeof(short), "integer")]
    [InlineData(typeof(byte), "integer")]
    [InlineData(typeof(float), "number")]
    [InlineData(typeof(double), "number")]
    [InlineData(typeof(decimal), "number")]
    [InlineData(typeof(string), "string")]
    [InlineData(typeof(string[]), "array")]
    [InlineData(typeof(List<int>), "array")]
    public void GetJsonSchemaTypeReturnsCorrectType(Type inputType, string expectedSchemaType)
    {
        // Act
        var result = AnthropicClientCore.GetJsonSchemaType(inputType);

        // Assert
        Assert.Equal(expectedSchemaType, result);
    }

    [Fact]
    public void GetJsonSchemaTypeReturnsStringForNull()
    {
        // Act
        var result = AnthropicClientCore.GetJsonSchemaType(null);

        // Assert
        Assert.Equal("string", result);
    }

    [Fact]
    public void GetJsonSchemaTypeHandlesNullableTypes()
    {
        // Act
        var intResult = AnthropicClientCore.GetJsonSchemaType(typeof(int?));
        var boolResult = AnthropicClientCore.GetJsonSchemaType(typeof(bool?));
        var doubleResult = AnthropicClientCore.GetJsonSchemaType(typeof(double?));

        // Assert
        Assert.Equal("integer", intResult);
        Assert.Equal("boolean", boolResult);
        Assert.Equal("number", doubleResult);
    }

    #endregion

    #region ConvertToolInputToKernelArguments Tests

    [Fact]
    public void ConvertToolInputToKernelArgumentsConvertsStringValue()
    {
        // Arrange
        var input = new Dictionary<string, JsonElement>
        {
            ["location"] = JsonSerializer.SerializeToElement("Seattle, WA")
        };

        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(input);

        // Assert
        Assert.Equal("Seattle, WA", result["location"]);
    }

    [Fact]
    public void ConvertToolInputToKernelArgumentsConvertsNumberValue()
    {
        // Arrange
        var input = new Dictionary<string, JsonElement>
        {
            ["count"] = JsonSerializer.SerializeToElement(42),
            ["temperature"] = JsonSerializer.SerializeToElement(0.7)
        };

        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(input);

        // Assert - ConvertJsonElementToObject returns long for integers
        Assert.Equal(42L, Convert.ToInt64(result["count"]));
        Assert.Equal(0.7, result["temperature"]);
    }

    [Fact]
    public void ConvertToolInputToKernelArgumentsConvertsBooleanValue()
    {
        // Arrange
        var input = new Dictionary<string, JsonElement>
        {
            ["enabled"] = JsonSerializer.SerializeToElement(true),
            ["disabled"] = JsonSerializer.SerializeToElement(false)
        };

        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(input);

        // Assert
        Assert.Equal(true, result["enabled"]);
        Assert.Equal(false, result["disabled"]);
    }

    [Fact]
    public void ConvertToolInputToKernelArgumentsConvertsNullValue()
    {
        // Arrange
        var input = new Dictionary<string, JsonElement>
        {
            ["nullValue"] = JsonSerializer.SerializeToElement<object?>(null)
        };

        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(input);

        // Assert
        Assert.Null(result["nullValue"]);
    }

    [Fact]
    public void ConvertToolInputToKernelArgumentsConvertsArrayValue()
    {
        // Arrange
        var input = new Dictionary<string, JsonElement>
        {
            ["items"] = JsonSerializer.SerializeToElement(new[] { "a", "b", "c" })
        };

        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(input);

        // Assert
        var items = result["items"] as object[];
        Assert.NotNull(items);
        Assert.Equal(3, items.Length);
        Assert.Equal("a", items[0]);
        Assert.Equal("b", items[1]);
        Assert.Equal("c", items[2]);
    }

    [Fact]
    public void ConvertToolInputToKernelArgumentsConvertsObjectValue()
    {
        // Arrange
        var input = new Dictionary<string, JsonElement>
        {
            ["config"] = JsonSerializer.SerializeToElement(new { name = "test", value = 123 })
        };

        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(input);

        // Assert
        var config = result["config"] as Dictionary<string, object?>;
        Assert.NotNull(config);
        Assert.Equal("test", config["name"]);
        Assert.Equal(123L, Convert.ToInt64(config["value"]));
    }

    [Fact]
    public void ConvertToolInputToKernelArgumentsReturnsEmptyForNull()
    {
        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(null);

        // Assert
        Assert.NotNull(result);
        Assert.Empty(result);
    }

    [Fact]
    public void ConvertToolInputToKernelArgumentsConvertsMultipleValues()
    {
        // Arrange
        var input = new Dictionary<string, JsonElement>
        {
            ["location"] = JsonSerializer.SerializeToElement("Seattle"),
            ["units"] = JsonSerializer.SerializeToElement("celsius"),
            ["days"] = JsonSerializer.SerializeToElement(5)
        };

        // Act
        var result = AnthropicClientCore.ConvertToolInputToKernelArguments(input);

        // Assert
        Assert.Equal(3, result.Count);
        Assert.Equal("Seattle", result["location"]);
        Assert.Equal("celsius", result["units"]);
        Assert.Equal(5L, Convert.ToInt64(result["days"]));
    }

    #endregion

    #region ConvertJsonElementToObject Tests

    [Fact]
    public void ConvertJsonElementToObjectConvertsString()
    {
        // Arrange
        var element = JsonSerializer.SerializeToElement("test string");

        // Act
        var result = AnthropicClientCore.ConvertJsonElementToObject(element);

        // Assert
        Assert.Equal("test string", result);
    }

    [Fact]
    public void ConvertJsonElementToObjectConvertsInteger()
    {
        // Arrange
        var element = JsonSerializer.SerializeToElement(42);

        // Act
        var result = AnthropicClientCore.ConvertJsonElementToObject(element);

        // Assert - The method returns long for integers
        Assert.Equal(42L, Convert.ToInt64(result));
    }

    [Fact]
    public void ConvertJsonElementToObjectConvertsDouble()
    {
        // Arrange
        var element = JsonSerializer.SerializeToElement(3.14159);

        // Act
        var result = AnthropicClientCore.ConvertJsonElementToObject(element);

        // Assert
        Assert.Equal(3.14159, result);
    }

    [Fact]
    public void ConvertJsonElementToObjectConvertsTrue()
    {
        // Arrange
        var element = JsonSerializer.SerializeToElement(true);

        // Act
        var result = AnthropicClientCore.ConvertJsonElementToObject(element);

        // Assert
        Assert.Equal(true, result);
    }

    [Fact]
    public void ConvertJsonElementToObjectConvertsFalse()
    {
        // Arrange
        var element = JsonSerializer.SerializeToElement(false);

        // Act
        var result = AnthropicClientCore.ConvertJsonElementToObject(element);

        // Assert
        Assert.Equal(false, result);
    }

    [Fact]
    public void ConvertJsonElementToObjectConvertsNull()
    {
        // Arrange
        var element = JsonSerializer.SerializeToElement<object?>(null);

        // Act
        var result = AnthropicClientCore.ConvertJsonElementToObject(element);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void ConvertJsonElementToObjectConvertsNestedObject()
    {
        // Arrange
        var element = JsonSerializer.SerializeToElement(new
        {
            outer = new { inner = "value" }
        });

        // Act
        var result = AnthropicClientCore.ConvertJsonElementToObject(element) as Dictionary<string, object?>;

        // Assert
        Assert.NotNull(result);
        var outer = result["outer"] as Dictionary<string, object?>;
        Assert.NotNull(outer);
        Assert.Equal("value", outer["inner"]);
    }

    #endregion
}

