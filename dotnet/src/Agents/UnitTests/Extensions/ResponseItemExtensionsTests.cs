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
public class ResponseItemExtensionsTests
{
    [Theory]
    [InlineData("CreateUserMessageItem", "user")]
    [InlineData("CreateAssistantMessageItem", "assistant")]
    [InlineData("CreateDeveloperMessageItem", "developer")]
    [InlineData("CreateSystemMessageItem", "system")]
    public void VerifyToChatMessageContentFromInputText(string creationMethod, string roleLabel)
    {
        // Arrange  
        string inputTextContent = "inputTextContent";
        MessageResponseItem responseItem = creationMethod switch
        {
            "CreateUserMessageItem" => ResponseItem.CreateUserMessageItem(inputTextContent),
            "CreateAssistantMessageItem" => ResponseItem.CreateAssistantMessageItem(inputTextContent),
            "CreateDeveloperMessageItem" => ResponseItem.CreateDeveloperMessageItem(inputTextContent),
            "CreateSystemMessageItem" => ResponseItem.CreateSystemMessageItem(inputTextContent),
            _ => throw new ArgumentException("Invalid creation method")
        };

        // Act  
        var messageContent = responseItem.ToChatMessageContent();

        // Assert  
        Assert.Equal(new AuthorRole(roleLabel), messageContent.Role);
        Assert.Single(messageContent.Items);
        Assert.IsType<TextContent>(messageContent.Items[0]);
        Assert.Equal(inputTextContent, ((TextContent)messageContent.Items[0]).Text);
    }

    [Fact]
    public void VerifyToChatMessageContentFromInputImage()
    {
        // Arrange
        IEnumerable<ResponseContentPart> contentParts = [ResponseContentPart.CreateInputImagePart("imageFileId")];
        MessageResponseItem responseItem = ResponseItem.CreateUserMessageItem(contentParts);

        // Act
        var messageContent = responseItem.ToChatMessageContent();

        // Assert
        Assert.Equal(AuthorRole.User, messageContent.Role);
        Assert.Single(messageContent.Items);
        Assert.IsType<FileReferenceContent>(messageContent.Items[0]);
        Assert.Equal("imageFileId", ((FileReferenceContent)messageContent.Items[0]).FileId);
    }

    [Fact]
    public void VerifyToChatMessageContentFromInputFile()
    {
        // Arrange
        var fileBytes = new ReadOnlyMemory<byte>([1, 2, 3, 4, 5]);
        IEnumerable<ResponseContentPart> contentParts = [ResponseContentPart.CreateInputFilePart("fileId", "fileName", new(fileBytes))];
        MessageResponseItem responseItem = ResponseItem.CreateUserMessageItem(contentParts);

        // Act
        var messageContent = responseItem.ToChatMessageContent();

        // Assert
        Assert.Equal(AuthorRole.User, messageContent.Role);
        Assert.Single(messageContent.Items);
        Assert.IsType<BinaryContent>(messageContent.Items[0]);
        Assert.Equal(fileBytes.ToArray(), ((BinaryContent)messageContent.Items[0]).Data?.ToArray());
    }

    [Fact]
    public void VerifyToChatMessageContentFromRefusal()
    {
        // Arrange
        IEnumerable<ResponseContentPart> contentParts = [ResponseContentPart.CreateRefusalPart("refusal")];
        MessageResponseItem responseItem = ResponseItem.CreateUserMessageItem(contentParts);

        // Act
        var messageContent = responseItem.ToChatMessageContent();

        // Assert
        Assert.Equal(AuthorRole.User, messageContent.Role);
        Assert.Single(messageContent.Items);
        Assert.IsType<TextContent>(messageContent.Items[0]);
        Assert.Equal("refusal", ((TextContent)messageContent.Items[0]).Text);
    }
}
