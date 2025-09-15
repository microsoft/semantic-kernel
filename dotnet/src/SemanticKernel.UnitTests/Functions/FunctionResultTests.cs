// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Linq;
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
        var openAICompletion = OpenAI.Chat.OpenAIChatModelFactory.ChatCompletion(
            role: OpenAI.Chat.ChatMessageRole.User,
            content: new OpenAI.Chat.ChatMessageContent(expectedValue));

        var valueType = new MEAI.ChatResponse(
            [
                new MEAI.ChatMessage(MEAI.ChatRole.User, expectedValue)
                {
                    RawRepresentation = openAICompletion.Content
                },
                new MEAI.ChatMessage(MEAI.ChatRole.Assistant, expectedValue)
                {
                    RawRepresentation = openAICompletion.Content
                }
            ])
        {
            RawRepresentation = openAICompletion
        };

        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert
        var message = target.GetValue<ChatMessageContent>()!;
        Assert.Equal(valueType.Messages.Last().Text, message.Content);
        Assert.Same(valueType.Messages.Last().RawRepresentation, message.InnerContent);
    }

    [Fact]
    public void GetValueConvertsFromSKChatMessageContentToMEAIChatMessage()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var openAIChatMessage = OpenAI.Chat.ChatMessage.CreateUserMessage(expectedValue);
        var valueType = new ChatMessageContent(AuthorRole.User, expectedValue) { InnerContent = openAIChatMessage };
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert
        Assert.Equal(valueType.Content, target.GetValue<MEAI.ChatMessage>()!.Text);
        Assert.Same(valueType.InnerContent, target.GetValue<MEAI.ChatMessage>()!.RawRepresentation);
    }

    [Fact]
    public void GetValueConvertsFromSKChatMessageContentToMEAIChatResponse()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var openAIChatMessage = OpenAI.Chat.ChatMessage.CreateUserMessage(expectedValue);
        var valueType = new ChatMessageContent(AuthorRole.User, expectedValue) { InnerContent = openAIChatMessage };
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert

        Assert.Equal(valueType.Content, target.GetValue<MEAI.ChatResponse>()!.Text);
        Assert.Same(valueType.InnerContent, target.GetValue<MEAI.ChatResponse>()!.Messages[0].RawRepresentation);
    }

    [Theory]
    [InlineData(1)]
    [InlineData(2)]
    [InlineData(5)]
    public void GetValueConvertsFromSKChatMessageContentListToMEAIChatResponse(int listSize)
    {
        // Arrange
        List<ChatMessageContent> multipleChoiceResponse = [];
        for (int i = 0; i < listSize; i++)
        {
            multipleChoiceResponse.Add(new ChatMessageContent(AuthorRole.User, Guid.NewGuid().ToString())
            {
                InnerContent = OpenAI.Chat.ChatMessage.CreateUserMessage(i.ToString())
            });
        }
        FunctionResult target = new(KernelFunctionFactory.CreateFromMethod(() => { }), (IReadOnlyList<ChatMessageContent>)multipleChoiceResponse);

        // Act and Assert
        // Ensure returns the ChatResponse for no choices as well
        var result = target.GetValue<MEAI.ChatResponse>()!;
        Assert.NotNull(result);

        for (int i = 0; i < listSize; i++)
        {
            // Ensure the other choices are not added as messages, only the first choice is considered
            Assert.Single(result.Messages);

            if (i == 0)
            {
                // The first choice is converted to a message
                Assert.Equal(multipleChoiceResponse[i].Content, result.Messages.Last().Text);
                Assert.Same(multipleChoiceResponse[i].InnerContent, result.Messages.Last().RawRepresentation);
            }
            else
            {
                // Any following choices messages are ignored and should not match the result message
                Assert.NotEqual(multipleChoiceResponse[i].Content, result.Text);
                Assert.NotSame(multipleChoiceResponse[i].InnerContent, result.Messages.Last().RawRepresentation);
            }
        }

        if (listSize > 0)
        {
            // Ensure the conversion to the first message works in one or multiple choice response
            Assert.Equal(multipleChoiceResponse[0].Content, target.GetValue<MEAI.ChatMessage>()!.Text);
            Assert.Same(multipleChoiceResponse[0].InnerContent, target.GetValue<MEAI.ChatMessage>()!.RawRepresentation);
        }
    }

    [Fact]
    public void GetValueThrowsForEmptyChoicesFromSKChatMessageContentListToMEAITypes()
    {
        // Arrange
        List<ChatMessageContent> multipleChoiceResponse = [];
        FunctionResult target = new(KernelFunctionFactory.CreateFromMethod(() => { }), (IReadOnlyList<ChatMessageContent>)multipleChoiceResponse);

        // Act and Assert
        var exception = Assert.Throws<InvalidCastException>(target.GetValue<MEAI.ChatResponse>);
        Assert.Contains("no choices", exception.Message);

        exception = Assert.Throws<InvalidCastException>(target.GetValue<MEAI.ChatMessage>);
        Assert.Contains("no choices", exception.Message);
    }

    [Fact]
    public void GetValueCanRetrieveMEAITypes()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var openAICompletion = OpenAI.Chat.OpenAIChatModelFactory.ChatCompletion(
            role: OpenAI.Chat.ChatMessageRole.User,
            content: new OpenAI.Chat.ChatMessageContent(expectedValue));

        var valueType = new MEAI.ChatResponse(
            new MEAI.ChatMessage(MEAI.ChatRole.User, expectedValue)
            {
                RawRepresentation = openAICompletion.Content
            })
        {
            RawRepresentation = openAICompletion
        };

        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert
        Assert.Same(valueType, target.GetValue<MEAI.ChatResponse>());
        Assert.Same(valueType.Messages[0], target.GetValue<MEAI.ChatMessage>());
        Assert.Same(valueType.Messages[0].Contents[0], target.GetValue<MEAI.TextContent>());
        Assert.Same(valueType.Messages[0].Contents[0], target.GetValue<MEAI.AIContent>());

        // Check the the content list is returned
        Assert.Same(valueType.Messages[0].Contents, target.GetValue<IList<MEAI.AIContent>>()!);
        Assert.Same(valueType.Messages[0].Contents[0], target.GetValue<IList<MEAI.AIContent>>()![0]);
        Assert.IsType<MEAI.TextContent>(target.GetValue<IList<MEAI.AIContent>>()![0]);

        // Check the raw representations are returned
        Assert.Same(valueType.RawRepresentation, target.GetValue<OpenAI.Chat.ChatCompletion>()!);
        Assert.Same(valueType.Messages[0].RawRepresentation, target.GetValue<OpenAI.Chat.ChatMessageContent>()!);
    }

    [Fact]
    public void GetValueThrowsForEmptyMessagesToMEAITypes()
    {
        // Arrange
        string expectedValue = Guid.NewGuid().ToString();
        var valueType = new MEAI.ChatResponse([]);
        FunctionResult target = new(s_nopFunction, valueType);

        // Act and Assert
        Assert.Empty(target.GetValue<MEAI.ChatResponse>()!.Messages);

        var exception = Assert.Throws<InvalidCastException>(target.GetValue<MEAI.ChatMessage>);
        Assert.Contains("no messages", exception.Message);

        exception = Assert.Throws<InvalidCastException>(target.GetValue<MEAI.TextContent>);
        Assert.Contains("no messages", exception.Message);

        exception = Assert.Throws<InvalidCastException>(target.GetValue<MEAI.AIContent>);
        Assert.Contains("no messages", exception.Message);
    }
}
