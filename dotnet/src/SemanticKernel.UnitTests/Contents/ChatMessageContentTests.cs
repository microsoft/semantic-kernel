// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.ChatCompletion;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;
public class ChatMessageContentTests
{
    [Fact]
    public void ConstructorShouldAddTextContentToItemsCollectionIfContentProvided()
    {
        // Arrange & act
        var sut = new ChatMessageContent(AuthorRole.User, "fake-content");

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is TextContent textContent && textContent.Text == "fake-content");
    }

    [Fact]
    public void ConstructorShouldNodAddTextContentToItemsCollectionIfNoContentProvided()
    {
        // Arrange & act
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Empty(sut.Items);
    }

    [Fact]
    public void ContentPropertySetterShouldAddTextContentToItemsCollection()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Act
        sut.Content = "fake-content";

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is TextContent textContent && textContent.Text == "fake-content");
    }

    [Fact]
    public void ContentPropertySetterShouldUpdateContentOfFirstTextContentItem()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123")));
        items.Add(new TextContent("fake-content-1"));
        items.Add(new TextContent("fake-content-2"));

        var sut = new ChatMessageContent(AuthorRole.User, items: items);

        // Act
        sut.Content = "fake-content-1-update";

        Assert.Equal("fake-content-1-update", ((TextContent)sut.Items[1]).Text);
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnNullIfThereAreNoTextContentItems()
    {
        // Arrange and act
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Null(sut.Content);
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnContentOfTextContentItem()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, "fake-content");

        // Act and assert
        Assert.Equal("fake-content", sut.Content);
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnContentOfTheFirstTextContentItem()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123")));
        items.Add(new TextContent("fake-content-1"));
        items.Add(new TextContent("fake-content-2"));

        var sut = new ChatMessageContent(AuthorRole.User, items: items);

        // Act and assert
        Assert.Equal("fake-content-1", sut.Content);
    }

    [Fact]
    public void ItShouldBePossibleToSetAndGetEncodingEvenIfThereAreNoItems()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Act
        sut.Encoding = Encoding.UTF32;

        // Assert
        Assert.Empty(sut.Items);
        Assert.Equal(Encoding.UTF32, sut.Encoding);
    }

    [Fact]
    public void EncodingPropertySetterShouldUpdateEncodingTextContentItem()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: "fake-content");

        // Act
        sut.Encoding = Encoding.UTF32;

        // Assert
        Assert.Single(sut.Items);
        Assert.Equal(Encoding.UTF32, ((TextContent)sut.Items[0]).Encoding);
    }

    [Fact]
    public void EncodingPropertyGetterShouldReturnEncodingOfTextContentItem()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: "fake-content");

        // Act
        ((TextContent)sut.Items[0]).Encoding = Encoding.Latin1;

        // Assert
        Assert.Equal(Encoding.Latin1, sut.Encoding);
    }
}
