// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
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
        ChatMessageContent? userMessageContent = userMessage.ToChatMessageContent();
        ChatMessageContent? functionCallContent = functionCall.ToChatMessageContent();

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

    /// <summary>
    /// Verify that ReasoningResponseItem with SummaryParts generates ReasoningContent correctly.
    /// </summary>
    [Fact]
    public void VerifyToChatMessageContentWithReasoningResponseItem()
    {
        // Arrange
        var reasoningResponseItem = this.CreateReasoningResponseItem("Let me think about this step by step...");

        // Act
        ChatMessageContent? chatMessageContent = reasoningResponseItem.ToChatMessageContent();

        // Assert
        Assert.NotNull(chatMessageContent);
        Assert.Equal(AuthorRole.Assistant, chatMessageContent.Role);
        Assert.Single(chatMessageContent.Items);

        var reasoningContent = chatMessageContent.Items[0] as ReasoningContent;
        Assert.NotNull(reasoningContent);
        Assert.Equal("Let me think about this step by step...", reasoningContent.Text);
    }

    /// <summary>
    /// Verify that ReasoningResponseItem converts to correct ChatMessageContentItemCollection with ReasoningContent.
    /// </summary>
    [Fact]
    public void VerifyToChatMessageContentItemCollectionWithReasoningResponseItem()
    {
        // Arrange
        var reasoningResponseItem = this.CreateReasoningResponseItem("Analyzing the problem...");

        // Act
        ChatMessageContentItemCollection collection = reasoningResponseItem.ToChatMessageContentItemCollection();

        // Assert
        Assert.NotNull(collection);
        Assert.Single(collection);
        Assert.IsType<ReasoningContent>(collection[0]);

        var reasoningContent = collection[0] as ReasoningContent;
        Assert.Equal("Analyzing the problem...", reasoningContent?.Text);
    }

    /// <summary>
    /// Verify that OpenAIResponse with both ReasoningResponseItem and MessageResponseItem generates correct content types.
    /// </summary>
    [Fact]
    public void VerifyToChatMessageContentWithMixedResponseItems()
    {
        // Arrange
        var reasoningResponseItem = this.CreateReasoningResponseItem("Thinking about the answer...");
        var messageResponseItem = ResponseItem.CreateAssistantMessageItem("Here is my response.");

        OpenAIResponse mockResponse = this.CreateMockOpenAIResponse("gpt-4o-mini",
            [
                reasoningResponseItem,
                messageResponseItem
            ]);

        // Act
        ChatMessageContent chatMessageContent = mockResponse.ToChatMessageContent();

        // Assert
        Assert.NotNull(chatMessageContent);
        Assert.Equal(2, chatMessageContent.Items.Count);

        // First item should be ReasoningContent
        Assert.IsType<ReasoningContent>(chatMessageContent.Items[0]);
        var reasoningContent = chatMessageContent.Items[0] as ReasoningContent;
        Assert.Equal("Thinking about the answer...", reasoningContent?.Text);

        // Second item should be TextContent
        Assert.IsType<TextContent>(chatMessageContent.Items[1]);
        var textContent = chatMessageContent.Items[1] as TextContent;
        Assert.Equal("Here is my response.", textContent?.Text);
    }

    #region private
    private OpenAIResponse CreateMockOpenAIResponse(string model, IEnumerable<ResponseItem> outputItems) =>
        OpenAIResponsesModelFactory.OpenAIResponse(
            model: model,
            outputItems: outputItems);

    private OpenAIResponse CreateMockOpenAIResponse(string id, DateTimeOffset createdAt, ResponseError error, string instructions, string model, string previousResponseId, float temperature, IEnumerable<ResponseTool> tools, float topP, IDictionary<string, string> metadata, ResponseIncompleteStatusDetails incompleteStatusDetails, IEnumerable<ResponseItem> outputItems, bool parallelToolCallsEnabled, ResponseToolChoice toolChoice) =>
        OpenAIResponsesModelFactory.OpenAIResponse(
            id: id,
            createdAt: createdAt,
            error: error,
            instructions: instructions,
            model: model,
            previousResponseId: previousResponseId,
            temperature: temperature,
            tools: tools,
            topP: topP,
            metadata: metadata,
            incompleteStatusDetails: incompleteStatusDetails,
            outputItems: outputItems,
            parallelToolCallsEnabled: parallelToolCallsEnabled,
            toolChoice: toolChoice);

    private ReasoningResponseItem CreateReasoningResponseItem(string? reasoningText = null) =>
        OpenAIResponsesModelFactory.ReasoningResponseItem(summaryText: reasoningText);

    #endregion
}
