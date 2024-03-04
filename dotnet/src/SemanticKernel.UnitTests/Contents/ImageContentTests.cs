// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

/// <summary>
/// Unit tests for <see cref="ImageContent"/> class.
/// </summary>
public sealed class ImageContentTests
{
    [Fact]
    public void ToStringForUriReturnsString()
    {
        // Arrange
        var content1 = new ImageContent((Uri)null!);
        var content2 = new ImageContent(new Uri("https://endpoint/"));

        // Act
        var result1 = content1.ToString();
        var result2 = content2.ToString();

        // Assert
        Assert.Empty(result1);
        Assert.Equal("https://endpoint/", result2);
    }

    [Fact]
    public void ToStringForDataUriReturnsDataUriString()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test");
        var content1 = new ImageContent(data) { MimeType = "text/plain" };

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal(dataUriToExpect, result1);
    }

    [Fact]
    public void ToStringForUriAndDataUriReturnsDataUriString()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test");
        var content1 = new ImageContent(data) { MimeType = "text/plain" };
        content1.Uri = new Uri("https://endpoint/");

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal(dataUriToExpect, result1);
    }

    [Fact]
    public void CreateForEmptyDataUriThrows()
    {
        // Arrange
        var data = BinaryData.Empty;

        // Assert
        Assert.Throws<ArgumentException>(() => new ImageContent(data) { MimeType = "text/plain" });
    }

    [Fact]
    public void ToStringForDataUriFromBytesReturnsDataUriString()
    {
        // Arrange
        var bytes = System.Text.Encoding.UTF8.GetBytes("this is a test");
        var data = BinaryData.FromBytes(bytes);
        var content1 = new ImageContent(data) { MimeType = "text/plain" };

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal(dataUriToExpect, result1);
    }

    [Fact]
    public void ToStringForDataUriFromStreamReturnsDataUriString()
    {
        // Arrange
        using var ms = new System.IO.MemoryStream(System.Text.Encoding.UTF8.GetBytes("this is a test"));
        var data = BinaryData.FromStream(ms);
        var content1 = new ImageContent(data) { MimeType = "text/plain" };

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal(dataUriToExpect, result1);

        // Assert throws if mediatype is null
        Assert.Throws<ArgumentException>(() => new ImageContent(BinaryData.FromStream(ms)) { MimeType = null! });
    }

    [Fact]
    public void InMemoryImageWithoutMediaTypeReturnsEmptyString()
    {
        // Arrange
        var sut = new ImageContent(new byte[] { 1, 2, 3 }) { MimeType = null };

        // Act
        var dataUrl = sut.ToString();

        // Assert
        Assert.Empty(dataUrl);
    }
}
