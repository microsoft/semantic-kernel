// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
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
        var assembly = type.Assembly;
        var internalServiceTierType = assembly.GetType("OpenAI.Internal.InternalServiceTier");
        var nullableInternalServiceTierType = typeof(Nullable<>).MakeGenericType(internalServiceTierType!);

        ConstructorInfo? constructor = type.GetConstructor(
            BindingFlags.Instance | BindingFlags.NonPublic,
            null,
            [
                typeof(IDictionary<string, string>),
                typeof(float?),
                typeof(float?),
                nullableInternalServiceTierType,
                typeof(string),
                typeof(bool?),
                typeof(string),
                typeof(IList<ResponseTool>),
                typeof(string),
                typeof(ResponseStatus?),
                typeof(DateTimeOffset),
                typeof(ResponseError),
                typeof(ResponseTokenUsage),
                typeof(string),
                typeof(ResponseReasoningOptions),
                typeof(int?),
                typeof(ResponseTextOptions),
                typeof(ResponseTruncationMode?),
                typeof(ResponseIncompleteStatusDetails),
                typeof(IList<ResponseItem>),
                typeof(bool),
                typeof(ResponseToolChoice),
                typeof(string),
                typeof(string),
                typeof(IDictionary<string, BinaryData>)
            ],
            null);

        if (constructor != null)
        {
            return (OpenAIResponse)constructor.Invoke(
                [
                    metadata,
                (float?)temperature,
                (float?)topP,
                null, // serviceTier
                previousResponseId,
                null, // background
                instructions,
                tools.ToList(),
                id,
                null, // status
                createdAt,
                error,
                null, // usage
                null, // endUserId
                null, // reasoningOptions
                null, // maxOutputTokenCount
                null, // textOptions
                null, // truncationMode
                incompleteStatusDetails,
                outputItems.ToList(),
                parallelToolCallsEnabled,
                toolChoice,
                model,
                "response",
                null // additionalBinaryDataProperties
                ]
            );
        }
        throw new InvalidOperationException("Constructor not found.");
    }

    private ReasoningResponseItem CreateReasoningResponseItem(string? reasoningText = null, IReadOnlyList<ReasoningSummaryPart>? summaryParts = null)
    {
        Type reasoningResponseItemType = typeof(ReasoningResponseItem);
        Type reasoningSummaryTextPartType = typeof(ReasoningSummaryTextPart);

        // If reasoningText is provided and summaryParts is not, create summaryParts with the text
        if (reasoningText != null && summaryParts == null)
        {
            // Try to find any public static factory method or constructor that can create ReasoningSummaryTextPart
            var createTextPartMethod = typeof(ReasoningSummaryPart).GetMethod(
                "CreateTextPart",
                BindingFlags.Static | BindingFlags.Public,
                null,
                [typeof(string)],
                null);

            if (createTextPartMethod != null)
            {
                var textPart = createTextPartMethod.Invoke(null, [reasoningText]) as ReasoningSummaryTextPart;
                summaryParts = textPart != null ? new List<ReasoningSummaryPart> { textPart } : new List<ReasoningSummaryPart>();
            }
            else
            {
                // Try to find constructor - search for all constructors
                var textPartConstructors = reasoningSummaryTextPartType.GetConstructors(
                    BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);

                ConstructorInfo? textPartConstructor = null;
                foreach (var ctor in textPartConstructors)
                {
                    var parameters = ctor.GetParameters();
                    if (parameters.Length >= 1 && parameters[0].ParameterType == typeof(string))
                    {
                        textPartConstructor = ctor;
                        break;
                    }
                }

                if (textPartConstructor != null)
                {
                    var ctorParams = textPartConstructor.GetParameters();
                    var args = new object?[ctorParams.Length];
                    args[0] = reasoningText;
                    // Fill in any additional parameters with null or default values
                    for (int i = 1; i < ctorParams.Length; i++)
                    {
                        args[i] = null;
                    }

                    var textPart = textPartConstructor.Invoke(args) as ReasoningSummaryTextPart;
                    summaryParts = textPart != null ? new List<ReasoningSummaryPart> { textPart } : new List<ReasoningSummaryPart>();
                }
                else
                {
                    throw new InvalidOperationException("Could not find a way to create ReasoningSummaryTextPart.");
                }
            }
        }

        // Convert null summaryParts to empty list for method calls
        var partsToPass = summaryParts ?? new List<ReasoningSummaryPart>();

        // Try to find a static factory method first
        var createReasoningItemMethod = typeof(ResponseItem).GetMethod(
            "CreateReasoningItem",
            BindingFlags.Static | BindingFlags.Public,
            null,
            [typeof(IEnumerable<ReasoningSummaryPart>)],
            null);

        if (createReasoningItemMethod != null)
        {
            return (ReasoningResponseItem)createReasoningItemMethod.Invoke(null, [partsToPass])!;
        }

        // If no factory method, look for constructors
        var constructors = reasoningResponseItemType.GetConstructors(
            BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public);

        foreach (var ctor in constructors)
        {
            var parameters = ctor.GetParameters();

            // Look for constructor that takes IReadOnlyList<ReasoningSummaryPart> or similar
            if (parameters.Length >= 1)
            {
                var firstParamType = parameters[0].ParameterType;
                if (firstParamType.IsAssignableFrom(typeof(List<ReasoningSummaryPart>)) ||
                    firstParamType.IsAssignableFrom(typeof(IReadOnlyList<ReasoningSummaryPart>)) ||
                    firstParamType.IsAssignableFrom(typeof(IEnumerable<ReasoningSummaryPart>)))
                {
                    var args = new object?[parameters.Length];
                    args[0] = partsToPass;
                    // Fill in any additional parameters with null
                    for (int i = 1; i < parameters.Length; i++)
                    {
                        args[i] = null;
                    }

                    return (ReasoningResponseItem)ctor.Invoke(args);
                }
            }
        }

        throw new InvalidOperationException("Constructor not found for ReasoningResponseItem.");
    }

    #endregion
}
