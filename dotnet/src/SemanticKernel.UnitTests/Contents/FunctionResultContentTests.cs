// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

public class FunctionResultContentTests
{
    private readonly FunctionCallContent _callContent;

    public FunctionResultContentTests()
    {
        this._callContent = new FunctionCallContent("f1", "p1", "id");
    }

    [Fact]
    public void ItShouldHaveFunctionIdInitialized()
    {
        // Arrange & act
        var sut = new FunctionResultContent(this._callContent, "result");

        // Assert
        Assert.Equal("id", sut.CallId);
    }

    [Fact]
    public void ItShouldHavePluginNameInitialized()
    {
        // Arrange & act
        var sut = new FunctionResultContent(this._callContent, "result");

        // Assert
        Assert.Equal("p1", sut.PluginName);
    }

    [Fact]
    public void ItShouldHaveFunctionNameInitialized()
    {
        // Arrange & act
        var sut = new FunctionResultContent(this._callContent, "result");

        // Assert
        Assert.Equal("f1", sut.FunctionName);
    }

    [Fact]
    public void ItShouldHaveFunctionResultInitialized()
    {
        // Arrange & act
        var sut = new FunctionResultContent(this._callContent, "result");

        // Assert
        Assert.Same("result", sut.Result);
    }

    [Fact]
    public void ItShouldHaveValueFromFunctionResultAsResultInitialized()
    {
        // Arrange & act
        var function = KernelFunctionFactory.CreateFromMethod(() => { });

        var functionResult = new FunctionResult(function, "result");

        var sut = new FunctionResultContent(this._callContent, functionResult);

        // Assert
        Assert.Equal("result", sut.Result);
    }

    [Fact]
    public void ItShouldBeSerializableAndDeserializable()
    {
        // Arrange
        var sut = new FunctionResultContent(this._callContent, "result");

        // Act
        var json = JsonSerializer.Serialize(sut);

        var deserializedSut = JsonSerializer.Deserialize<FunctionResultContent>(json);

        // Assert
        Assert.NotNull(deserializedSut);
        Assert.Equal(sut.CallId, deserializedSut.CallId);
        Assert.Equal(sut.PluginName, deserializedSut.PluginName);
        Assert.Equal(sut.FunctionName, deserializedSut.FunctionName);
        Assert.Equal(sut.Result, deserializedSut.Result?.ToString());
    }

    [Fact]
    public void ItShouldCreateChatMessageContent()
    {
        // Arrange
        var sut = new FunctionResultContent(this._callContent, "result");

        // Act
        var chatMessageContent = sut.ToChatMessage();

        // Assert
        Assert.NotNull(chatMessageContent);
        Assert.Single(chatMessageContent.Items);
        Assert.Same(sut, chatMessageContent.Items[0]);
    }
}
