// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;
using MEAI = Microsoft.Extensions.AI;

namespace SemanticKernel.UnitTests.Functions;

/// <summary>
/// Unit tests of <see cref="FunctionResult"/>.
/// </summary>
public class FunctionResultTests
{
    private static readonly KernelFunction s_nopFunction = KernelFunctionFactory.CreateFromMethod(() => { });

    [Fact]
    public void DefaultsAreExpected()
    {
        var result = new FunctionResult(s_nopFunction);
        Assert.Null(result.GetValue<object>());
        Assert.Same(CultureInfo.InvariantCulture, result.Culture);
        Assert.Null(result.Metadata);
    }

    [Fact]
    public void PropertiesRoundtrip()
    {
        object resultValue = new();
        CultureInfo culture = new("fr-FR");
        var metadata = new Dictionary<string, object?>();

        FunctionResult result = new(s_nopFunction, resultValue, culture);
        Assert.Same(resultValue, result.GetValue<object>());
        Assert.Same(culture, result.Culture);
        Assert.Null(result.Metadata);

        result = new(s_nopFunction, resultValue, culture, metadata);
        Assert.Same(resultValue, result.GetValue<object>());
        Assert.Same(culture, result.Culture);
        Assert.Same(metadata, result.Metadata);
    }

    [Fact]
    public void GetValueReturnsValueWhenValueIsNotNull()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Act,Assert
        Assert.Equal(value, target.GetValue<string>());
    }

    [Fact]
    public void GetValueReturnsNullWhenValueIsNull()
    {
        // Arrange
        FunctionResult target = new(s_nopFunction);

        // Act,Assert
        Assert.Null(target.GetValue<string>());
    }

    [Fact]
    public void GetValueThrowsWhenValueIsNotNullButTypeDoesNotMatch()
    {
        // Arrange
        int value = 42;
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Act,Assert
        Assert.Throws<InvalidCastException>(target.GetValue<string>);
    }

    [Fact]
    public void ConstructorSetsProperties()
    {
        // Act
        FunctionResult target = new(s_nopFunction);

        // Assert
        Assert.Same(s_nopFunction, target.Function);
    }

    [Fact]
    public void ConstructorSetsPropertiesAndValue()
    {
        // Arrange
        string functionName = Guid.NewGuid().ToString();
        string value = Guid.NewGuid().ToString();

        // Act
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Assert
        Assert.Same(s_nopFunction, target.Function);
        Assert.Equal(value, target.Value);
    }

    [Fact]
    public void ToStringWorksCorrectly()
    {
        // Arrange
        string value = Guid.NewGuid().ToString();
        FunctionResult target = new(s_nopFunction, value, CultureInfo.InvariantCulture);

        // Act and Assert
        Assert.Equal(value, target.ToString());
    }

    [Fact]
    public void GetValueWhenValueIsKernelContentGenericStringShouldReturnContentBaseToString()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        FunctionResult target = new(s_nopFunction, new TextContent(expectedValue));

        // Act and Assert
        Assert.Equal(expectedValue, target.GetValue<string>());
    }

    [Fact]
    public void GetValueWhenValueIsKernelContentGenericTypeMatchShouldReturn()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new TextContent(expectedValue);
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert

        Assert.Equal(valueType, target.GetValue<TextContent>());
        Assert.Equal(valueType, target.GetValue<KernelContent>());
    }

    [Fact]
    public void GetValueConvertsFromMEAIChatMessageToSKChatMessageContent()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new MEAI.ChatResponse(new MEAI.ChatMessage(MEAI.ChatRole.User, expectedValue));
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert

        Assert.Equal(valueType.Message.Text, target.GetValue<ChatMessageContent>()!.Content);
    }

    [Fact]
    public void GetValueConvertsFromSKChatMessageContentToMEAIChatMessage()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new ChatMessageContent(AuthorRole.User, expectedValue);
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert

        Assert.Equal(valueType.Content, target.GetValue<MEAI.ChatMessage>()!.Text);
    }

    [Fact]
    public void GetValueConvertsFromSKChatMessageContentToMEAIChatResponse()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new ChatMessageContent(AuthorRole.User, expectedValue);
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert

        Assert.Equal(valueType.Content, target.GetValue<MEAI.ChatResponse>()!.Message.Text);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(10)]
    public void GetValueConvertsFromSKChatMessageContentListToMEAIChatResponse(int listSize)
    {
        // Arrange
        List<ChatMessageContent> valueType = [];
        for (int i = 0; i < listSize; i++)
        {
            valueType.Add(new ChatMessageContent(AuthorRole.User, Guid.NewGuid().ToString()));
        }
        FunctionResult target = new(KernelFunctionFactory.CreateFromMethod(() => { }), valueType);

        // Act and Assert
        var result = target.GetValue<MEAI.ChatResponse>()!;
        for (int i = 0; i < listSize; i++)
        {
            Assert.Equal(valueType[i].Content, result.Choices[i].Text);
        }
        Assert.Equal(valueType.Count, result.Choices.Count);
    }

    [Fact]
    public void GetValueCanRetrieveMEAITypes()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new MEAI.ChatResponse(new MEAI.ChatMessage(MEAI.ChatRole.User, expectedValue));
        FunctionResult target = new(s_nopFunction, valueType);
        // Act and Assert
        Assert.Same(valueType, target.GetValue<MEAI.ChatResponse>());
        Assert.Same(valueType.Message, target.GetValue<MEAI.ChatMessage>());
        Assert.Same(valueType.Message.Contents[0], target.GetValue<MEAI.TextContent>());
        Assert.Same(valueType.Message.Contents[0], target.GetValue<MEAI.AIContent>());
    }

    [Fact]
    public void GetValueIsNullForEmptyChoicesMEAITypes()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new MEAI.ChatResponse([]);
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert
        Assert.Empty(target.GetValue<MEAI.ChatResponse>()!.Choices);
        Assert.Null(target.GetValue<MEAI.ChatMessage>());
        Assert.Null(target.GetValue<MEAI.TextContent>());
        Assert.Null(target.GetValue<MEAI.AIContent>());
    }
}
