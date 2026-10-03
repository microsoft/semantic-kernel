// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Agents.OpenAI;
using Microsoft.SemanticKernel.ChatCompletion;
using OpenAI.Responses;
using Xunit;

namespace SemanticKernel.Agents.UnitTests.OpenAI.Extensions;

/// <summary>
/// Unit tests for ChatContentMessageExtensions
/// </summary>
public class ChatContentMessageExtensionsTests
{
    [Theory]
    [InlineData("User")]
    [InlineData("Assistant")]
    [InlineData("System")]
    public void VerifyToResponseItemWithUserChatMessageContent(string roleLabel)
    {
        // Arrange
        var role = new AuthorRole(roleLabel);
        var content = new ChatMessageContent(
                role,
                items: [
                    new TextContent("What is in this image?"),
                    new ImageContent(new Uri("https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg")),
                    new BinaryContent(new ReadOnlyMemory<byte>([0x52, 0x49, 0x46, 0x46, 0x24, 0x08, 0x00, 0x00, 0x57, 0x41, 0x56, 0x45]), "audio/wav"),
                    new FileReferenceContent("file-abc123")
                ]
            );

        // Act
        var responseItem = content.ToResponseItem();

        // Assert
        Assert.NotNull(responseItem);
        Assert.IsType<MessageResponseItem>(responseItem, exactMatch: false);
        var messageResponseItem = responseItem as MessageResponseItem;
        Assert.NotNull(messageResponseItem);
        Assert.Equal(role.Label.ToUpperInvariant(), messageResponseItem.Role.ToString().ToUpperInvariant());
        Assert.Equal(4, messageResponseItem.Content.Count);

        // Determine expected kind for text content based on role
        var expectedTextKind = roleLabel.Equals("assistant", StringComparison.OrdinalIgnoreCase)
            ? ResponseContentPartKind.OutputText
            : ResponseContentPartKind.InputText;

        // Validate TextContent conversion - should create appropriate Input/OutputText part
        var textContent = messageResponseItem.Content.FirstOrDefault(p => p.Kind == expectedTextKind);
        Assert.NotNull(textContent);
        Assert.Equal("What is in this image?", textContent.Text);

        // Validate ImageContent conversion - should create InputImage part
        var imageContent = messageResponseItem.Content.FirstOrDefault(p => p.Kind == ResponseContentPartKind.InputImage);
        Assert.NotNull(imageContent);

        // Validate BinaryContent conversion - should create InputFile part
        var binaryContent = messageResponseItem.Content.FirstOrDefault(p => p.Kind == ResponseContentPartKind.InputFile && p.InputFileBytes is not null);
        Assert.NotNull(binaryContent);
        Assert.Equal("audio/wav", binaryContent.InputFileBytesMediaType);

        // Validate FileReferenceContent conversion - should create InputImage part
        var fileContent = messageResponseItem.Content.FirstOrDefault(p => p.Kind == ResponseContentPartKind.InputFile && p.InputFileId is not null);
        Assert.NotNull(fileContent);
        Assert.Equal("file-abc123", fileContent.InputFileId);
    }
}
