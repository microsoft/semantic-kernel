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
        var data = BinaryData.FromString("this is a test", "text/plain");
        var content1 = new ImageContent(data);

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:{data.MediaType};base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal(dataUriToExpect, result1);
    }

    [Fact]
    public void ToStringForUriAndDataUriReturnsDataUriString()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test", "text/plain");
        var content1 = new ImageContent(data);
        content1.Uri = new Uri("https://endpoint/");

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:{data.MediaType};base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal(dataUriToExpect, result1);
    }

    [Fact]
    public void CreateForNullDataUriOrWithoutMediaTypeThrows()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test", null);
        var data2 = BinaryData.FromString("this is a test", string.Empty);
        var data3 = BinaryData.FromString("this is a test", " ");

        // Assert
        Assert.Throws<ArgumentNullException>(() => new ImageContent((BinaryData)null!));
        Assert.Throws<ArgumentNullException>(() => new ImageContent(data));
        Assert.Throws<ArgumentNullException>(() => new ImageContent(data2));
        Assert.Throws<ArgumentNullException>(() => new ImageContent(data3));
    }

    [Fact]
    public void CreateForEmptyDataUriThrows()
    {
        // Arrange
        var data = BinaryData.Empty;

        // Assert
        Assert.Throws<ArgumentNullException>(() => new ImageContent(data));
    }

    [Fact]
    public void ToStringForDataUriFromBytesReturnsDataUriString()
    {
        // Arrange
        var bytes = System.Text.Encoding.UTF8.GetBytes("this is a test");
        var data = BinaryData.FromBytes(bytes, "text/plain");
        var content1 = new ImageContent(data);

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:{data.MediaType};base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal(dataUriToExpect, result1);

        // Assert throws if mediatype is null
        Assert.Throws<ArgumentNullException>(() => new ImageContent(BinaryData.FromBytes(bytes, null)));
        Assert.Throws<ArgumentNullException>(() => new ImageContent(BinaryData.FromBytes(bytes, string.Empty)));
        Assert.Throws<ArgumentNullException>(() => new ImageContent(BinaryData.FromBytes(bytes, " ")));
    }

    [Fact]
    public void ToStringForDataUriFromStreamReturnsDataUriString()
    {
        // Arrange
        var ms = new System.IO.MemoryStream(System.Text.Encoding.UTF8.GetBytes("this is a test"));
        try
        {
            var data = BinaryData.FromStream(ms, "text/plain");
            var content1 = new ImageContent(data);

            // Act
            var result1 = content1.ToString();
            var dataUriToExpect = $"data:{data.MediaType};base64,{Convert.ToBase64String(data.ToArray())}";

            // Assert
            Assert.Equal(dataUriToExpect, result1);

            // Assert throws if mediatype is null
            Assert.Throws<ArgumentNullException>(() => new ImageContent(BinaryData.FromStream(ms, null)));
        }
        finally
        {
            ms.Dispose();
        }
    }
}
