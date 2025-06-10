// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Reflection;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit testing of <see cref="Microsoft.SemanticKernel.Agents.OpenAI.OpenAIResponseExtensions"/>.
/// </summary>
public class OpenAIResponseExtensionsTests
{
    /// <summary>
    /// Verify conversion from <see cref="OpenAIResponse"/> to <see cref="ChatMessageContent"/>.
    /// </summary>
    [Fact]
    public void VerifyToChatMessageContentWithOpenAIResponse()
    {
        // Arrange
        OpenAIResponse mockResponse = this.CreateMockOpenAIResponse("gpt-4o-mini",
            [
                ResponseItem.CreateUserMessageItem("This is a user message."),
            ]);

        // Act
        ChatMessageContent chatMessageContent = mockResponse.ToChatMessageContent();

        // Assert
        Assert.NotNull(chatMessageContent);
        Assert.Equal(AuthorRole.User, chatMessageContent.Role);
        Assert.Equal("gpt-4o-mini", chatMessageContent.ModelId);
        Assert.Single(chatMessageContent.Items);
        Assert.Equal("This is a user message.", chatMessageContent.Items[0].ToString());
    }

    /// <summary>
    /// Verify conversion from <see cref="ResponseItem"/> to <see cref="ChatMessageContent"/>.
    /// </summary>
    [Fact]
    public void VerifyToChatMessageContentWithResponseItem()
    {
        // Arrange
        ResponseItem userMessage = ResponseItem.CreateUserMessageItem("This is a user message.");
        ResponseItem functionCall = ResponseItem.CreateFunctionCallItem("callId", "functionName", new BinaryData("{}"));

        // Act
        ChatMessageContent userMessageContent = userMessage.ToChatMessageContent();
        ChatMessageContent functionCallContent = functionCall.ToChatMessageContent();

        // Assert
        Assert.NotNull(userMessageContent);
        Assert.Equal(AuthorRole.User, userMessageContent.Role);
        Assert.Single(userMessageContent.Items);
        Assert.Equal("This is a user message.", userMessageContent.Items[0].ToString());
        Assert.NotNull(functionCallContent);
        Assert.Equal(AuthorRole.Assistant, functionCallContent.Role);
        Assert.Single(functionCallContent.Items);
        Assert.IsType<FunctionCallContent>(functionCallContent.Items[0]);
    }

    /// <summary>
    /// Verify conversion from <see cref="MessageResponseItem"/> to <see cref="ChatMessageContent"/>.
    /// </summary>
    [Fact]
    public void VerifyToChatMessageContentItemCollectionWithMessageResponseItem()
    {
        // Arrange
        ResponseItem responseItem = ResponseItem.CreateUserMessageItem("This is a user message.");

        // Act
        ChatMessageContentItemCollection collection = responseItem.ToChatMessageContentItemCollection();

        // Assert
        Assert.NotNull(collection);
        Assert.Single(collection);
        Assert.NotNull(collection[0]);
        Assert.IsType<TextContent>(collection[0]);
        Assert.Equal("This is a user message.", collection[0].ToString());
    }

    /// <summary>
    /// Verify conversion from <see cref="FunctionCallResponseItem"/> to <see cref="ChatMessageContent"/>.
    /// </summary>
    [Fact]
    public void VerifyToChatMessageContentItemCollectionWithFunctionCallResponseItem()
    {
        // Arrange
        FunctionCallResponseItem responseItem = FunctionCallResponseItem.CreateFunctionCallItem("callId", "functionName", new BinaryData("{}"));

        // Act
        ChatMessageContentItemCollection collection = responseItem.ToChatMessageContentItemCollection();

        // Assert
        Assert.NotNull(collection);
        Assert.Single(collection);
        Assert.NotNull(collection[0]);
        Assert.IsType<FunctionCallContent>(collection[0]);
    }

    /// <summary>
    /// Verify conversion from <see cref="FunctionCallResponseItem"/> to <see cref="StreamingFunctionCallUpdateContent"/>.
    /// </summary>
    [Fact]
    public void VerifyToStreamingFunctionCallUpdateContent()
    {
        // Arrange
        FunctionCallResponseItem responseItem = FunctionCallResponseItem.CreateFunctionCallItem("callId", "functionName", new BinaryData("{}"));

        // Act
        StreamingFunctionCallUpdateContent content = responseItem.ToStreamingFunctionCallUpdateContent("{}");

        // Assert
        Assert.NotNull(content);
        Assert.Equal("functionName", content.Name);
        Assert.Equal("callId", content.CallId);
        Assert.NotNull(content.Arguments);
    }

    /// <summary>
    /// Verify conversion from <see cref="MessageRole"/> to <see cref="AuthorRole"/>.
    /// </summary>
    [Fact]
    public void VerifyToAuthorRole()
    {
        // Act & Assert
        Assert.Equal(AuthorRole.Assistant, MessageRole.Assistant.ToAuthorRole());
        Assert.Equal(AuthorRole.User, MessageRole.User.ToAuthorRole());
        Assert.Equal(AuthorRole.Developer, MessageRole.Developer.ToAuthorRole());
        Assert.Equal(AuthorRole.System, MessageRole.System.ToAuthorRole());
    }

    /// <summary>
    /// Verify conversion from <see cref="FunctionCallResponseItem"/> to <see cref="FunctionCallContent"/>.
    /// </summary>
    [Fact]
    public void VerifyToFunctionCallContent()
    {
        // Arrange
        FunctionCallResponseItem responseItem = FunctionCallResponseItem.CreateFunctionCallItem("callId", "functionName", new BinaryData("{}"));

        // Act
        FunctionCallContent content = responseItem.ToFunctionCallContent();

        // Assert
        Assert.NotNull(content);
        Assert.Equal("functionName", content.FunctionName);
        Assert.Equal("callId", content.Id);
        Assert.NotNull(content.Arguments);
    }

    #region private
    private OpenAIResponse CreateMockOpenAIResponse(string model, IEnumerable<ResponseItem> outputItems)
    {
#pragma warning disable CS8625 // Cannot convert null literal to non-nullable reference type.
        return this.CreateMockOpenAIResponse(
            "id",
            DateTimeOffset.Now,
            null,
            "instructions",
            model,
            "previousResponseId",
            0,
            [],
            0,
            null,
            null,
            outputItems,
            false,
            ResponseToolChoice.CreateAutoChoice());
#pragma warning restore CS8625 // Cannot convert null literal to non-nullable reference type.
    }
    private OpenAIResponse CreateMockOpenAIResponse(string id, DateTimeOffset createdAt, ResponseError error, string instructions, string model, string previousResponseId, float temperature, IEnumerable<ResponseTool> tools, float topP, IDictionary<string, string> metadata, ResponseIncompleteStatusDetails incompleteStatusDetails, IEnumerable<ResponseItem> outputItems, bool parallelToolCallsEnabled, ResponseToolChoice toolChoice)
    {
        Type type = typeof(OpenAIResponse);

        ConstructorInfo? constructor = type.GetConstructor(
            BindingFlags.Instance | BindingFlags.NonPublic,
            null,
            [
                typeof(string),
                typeof(DateTimeOffset),
                typeof(ResponseError),
                typeof(string),
                typeof(string),
                typeof(string),
                typeof(float),
                typeof(IEnumerable<ResponseTool>),
                typeof(float),
                typeof(IDictionary<string, string>),
                typeof(ResponseIncompleteStatusDetails),
                typeof(IEnumerable<ResponseItem>),
                typeof(bool),
                typeof(ResponseToolChoice)
            ],
            null);

        if (constructor != null)
        {
            return (OpenAIResponse)constructor.Invoke(
                [
                    id,
                    createdAt,
                    error,
                    instructions,
                    model,
                    previousResponseId,
                    temperature,
                    tools,
                    topP,
                    metadata,
                    incompleteStatusDetails,
                    outputItems,
                    parallelToolCallsEnabled,
                    toolChoice
                ]
            );
        }
        throw new InvalidOperationException("Constructor not found.");
    }

    #endregion
}
