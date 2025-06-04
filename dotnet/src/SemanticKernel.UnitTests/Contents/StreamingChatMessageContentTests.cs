// Copyright (c) Microsoft. All rights reserved.

using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;
public class StreamingChatMessageContentTests
{
    [Fact]
    public void ConstructorShouldAddTextContentToItemsCollectionIfContentProvided()
    {
        // Arrange & act
        var sut = new StreamingChatMessageContent(AuthorRole.User, "fake-content");

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is StreamingTextContent textContent && textContent.Text == "fake-content");
    }

    [Fact]
    public void ConstructorShouldNodAddTextContentToItemsCollectionIfNoContentProvided()
    {
        // Arrange & act
        var sut = new StreamingChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Empty(sut.Items);
    }

    [Fact]
    public void ContentPropertySetterShouldAddTextContentToItemsCollection()
    {
        // Arrange
        var sut = new StreamingChatMessageContent(AuthorRole.User, content: null)
        {
            Content = "fake-content"
        };

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is StreamingTextContent textContent && textContent.Text == "fake-content");
    }

    [Fact]
    public void ContentPropertySetterShouldNotAddTextContentToItemsCollection()
    {
        // Arrange
        var sut = new StreamingChatMessageContent(AuthorRole.User, content: null)
        {
            Content = null
        };

        // Assert
        Assert.Empty(sut.Items);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("content-update")]
    public void ContentPropertySetterShouldUpdateContentOfFirstTextContentItem(string? content)
    {
        // Arrange
        var items = new StreamingKernelContentItemCollection
        {
            new StreamingTextContent("fake-content-1"),
            new StreamingTextContent("fake-content-2")
        };

        var sut = new StreamingChatMessageContent(AuthorRole.User, content: null);
        sut.Items = items;
        sut.Content = content;

        Assert.Equal(content, ((StreamingTextContent)sut.Items[0]).Text);
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnNullIfThereAreNoTextContentItems()
    {
        // Arrange and act
        var sut = new StreamingChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Null(sut.Content);
        Assert.Equal(string.Empty, sut.ToString());
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnContentOfTextContentItem()
    {
        // Arrange
        var sut = new StreamingChatMessageContent(AuthorRole.User, "fake-content");

        // Act and assert
        Assert.Equal("fake-content", sut.Content);
        Assert.Equal("fake-content", sut.ToString());
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnContentOfTheFirstTextContentItem()
    {
        // Arrange
        var items = new StreamingKernelContentItemCollection
        {
            new StreamingTextContent("fake-content-1"),
            new StreamingTextContent("fake-content-2")
        };

        var sut = new StreamingChatMessageContent(AuthorRole.User, content: null)
        {
            Items = items
        };

        // Act and assert
        Assert.Equal("fake-content-1", sut.Content);
    }

    [Theory]
    [InlineData(null)]
    [InlineData("")]
    [InlineData(" ")]
    [InlineData("\t")]
    [InlineData("\n")]
    [InlineData("\r\n")]
    public void ContentPropertySetterShouldConvertEmptyOrWhitespaceAuthorNameToNull(string? authorName)
    {
        // Arrange
        var message = new StreamingChatMessageContent(AuthorRole.User, content: null)
        {
            AuthorName = authorName
        };

        // Assert
        Assert.Null(message.AuthorName);
    }

    [Fact]
    public void ItShouldBePossibleToSetAndGetEncodingEvenIfThereAreNoItems()
    {
        // Arrange
        var sut = new StreamingChatMessageContent(AuthorRole.User, content: null)
        {
            Encoding = Encoding.UTF32
        };

        // Assert
        Assert.Empty(sut.Items);
        Assert.Equal(Encoding.UTF32, sut.Encoding);
    }

    [Fact]
    public void EncodingPropertySetterShouldUpdateEncodingTextContentItem()
    {
        // Arrange
        var sut = new StreamingChatMessageContent(AuthorRole.User, content: "fake-content")
        {
            Encoding = Encoding.UTF32
        };

        // Assert
        Assert.Single(sut.Items);
        Assert.Equal(Encoding.UTF32, ((StreamingTextContent)sut.Items[0]).Encoding);
    }

    [Fact]
    public void EncodingPropertyGetterShouldReturnEncodingOfTextContentItem()
    {
        // Arrange
        var sut = new StreamingChatMessageContent(AuthorRole.User, content: "fake-content");

        // Act
        ((StreamingTextContent)sut.Items[0]).Encoding = Encoding.Latin1;

        // Assert
        Assert.Equal(Encoding.Latin1, sut.Encoding);
    }
}
