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
    public void ConstructorShouldAddTextContentAsFirstItemIfContentProvided()
    {
        // Arrange & act
        var sut = new ChatMessageContent(AuthorRole.User, "fake-content");

        // Assert
        Assert.Single(sut.Items);

        Assert.Contains(sut.Items, item => item is TextContent textContent && textContent.Text == "fake-content");
    }

    [Fact]
    public void ConstructorShouldNodAddTextContentAsFirstItemIfNoContentProvided()
    {
        // Arrange & act
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Empty(sut.Items);
    }

    [Fact]
    public void ContentPropertySetterShouldAddTextContentAsFirstItemIfThereAreNoItems()
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
    public void ContentPropertySetterShouldUpdateContentOfFirstItemIfItIsOfTextContentType()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: "initial-fake-content");

        // Act
        sut.Content = "fake-content";

        // Assert
        Assert.Single(sut.Items);
        Assert.Equal("fake-content", ((TextContent)sut.Items[0]).Text);
    }

    [Fact]
    public void ContentPropertySetterShouldRejectUpdatingContentOfFirstItemIfItIsNotOfTextContentType()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123")));

        var sut = new ChatMessageContent(AuthorRole.User, items: items);

        // Act
        Assert.Throws<InvalidOperationException>(() => sut.Content = "fake-content");
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnNullIfThereAreNoItems()
    {
        // Arrange and act
        var sut = new ChatMessageContent(AuthorRole.User, content: null);

        // Assert
        Assert.Null(sut.Content);
    }

    [Fact]
    public void ContentPropertyGetterShouldReturnContentOfFirstItemIfItIsOfTextContentType()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, "fake-content");

        // Act and assert
        Assert.Equal("fake-content", sut.Content);
    }

    [Fact]
    public void ContentPropertyGetterShouldRejectReturningContentOfFirstItemIfItIsNotOfTextContentType()
    {
        // Arrange
        var items = new ChatMessageContentItemCollection();
        items.Add(new ImageContent(new Uri("https://fake-random-test-host:123")));

        var sut = new ChatMessageContent(AuthorRole.User, items: items);

        // Act and assert
        Assert.Throws<InvalidOperationException>(() => sut.Content == "fake-content");
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
    public void EncodingPropertySetterShouldUpdateEncodingOfFirstItemIfItIsOfTextContentType()
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
    public void EncodingPropertyGetterShouldReturnEncodingOfFirstItemIfItIsOfTextContentType()
    {
        // Arrange
        var sut = new ChatMessageContent(AuthorRole.User, content: "fake-content");

        // Act
        ((TextContent)sut.Items[0]).Encoding = Encoding.Latin1;

        // Assert
        Assert.Equal(Encoding.Latin1, sut.Encoding);
    }
}
