// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
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
        Assert.Equal($"Microsoft.SemanticKernel.{nameof(ImageContent)}", result1);
        Assert.Equal($"Microsoft.SemanticKernel.{nameof(ImageContent)}", result2);
    }

    [Fact]
    public void ToStringForDataUriReturnsTypeString()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test");
        var content1 = new ImageContent(data, "text/plain");

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal($"Microsoft.SemanticKernel.{nameof(ImageContent)}", result1);
    }

    [Fact]
    public void ToStringForUriAndDataUriReturnsDataUriString()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test");
        var content1 = new ImageContent(data, "text/plain") { Uri = new Uri("https://endpoint/") };

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal($"Microsoft.SemanticKernel.{nameof(ImageContent)}", result1);
    }

    [Fact]
    public void CreateForEmptyDataUriThrows()
    {
        // Arrange
        var data = BinaryData.Empty;

        // Assert
        Assert.Throws<ArgumentException>(()
            => new ImageContent(data, "text/plain"));
    }

    [Fact]
    public void ToStringForDataUriFromBytesReturnsType()
    {
        // Arrange
        var bytes = System.Text.Encoding.UTF8.GetBytes("this is a test");
        var data = BinaryData.FromBytes(bytes);
        var content1 = new ImageContent(data, "text/plain");

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal($"Microsoft.SemanticKernel.{nameof(ImageContent)}", result1);
    }

    [Fact]
    public void ToStringForDataUriFromStreamReturnsDataUriString()
    {
        // Arrange
        using var ms = new System.IO.MemoryStream(System.Text.Encoding.UTF8.GetBytes("this is a test"));
        var data = BinaryData.FromStream(ms);
        var content1 = new ImageContent(data, "text/plain");

        // Act
        var result1 = content1.ToString();
        var dataUriToExpect = $"data:text/plain;base64,{Convert.ToBase64String(data.ToArray())}";

        // Assert
        Assert.Equal($"Microsoft.SemanticKernel.{nameof(ImageContent)}", result1);
    }

    [Fact]
    public void DataConstructorWhenDataIsEmptyShouldThrow()
    {
        // Arrange
        using var ms = new System.IO.MemoryStream(System.Text.Encoding.UTF8.GetBytes("this is a test"));

        var data = BinaryData.FromStream(ms);

        // Assert throws if mediatype is null
        Assert.Throws<ArgumentException>(() => new ImageContent(BinaryData.FromStream(ms), mimeType: null));
    }

    [Fact]
    public void ToStringInMemoryImageWithoutMediaTypeReturnsType()
    {
        // Arrange
        var sut = new ImageContent(new byte[] { 1, 2, 3 }, mimeType: null);

        // Act
        var dataUrl = sut.ToString();

        // Assert
        Assert.Equal($"Microsoft.SemanticKernel.{nameof(ImageContent)}", dataUrl?.ToString());
    }

    // Ensure retrocompatibility with ImageContent Pre-BinaryContent Version

    [Theory]
    [InlineData("", null, $"Microsoft.SemanticKernel.{nameof(ImageContent)}")]
    [InlineData(null, null, $"Microsoft.SemanticKernel.{nameof(ImageContent)}")]
    [InlineData("", "http://localhost:9090/", $"Microsoft.SemanticKernel.{nameof(ImageContent)}")]
    [InlineData(null, "http://localhost:9090/", $"Microsoft.SemanticKernel.{nameof(ImageContent)}")]
    [InlineData("image/png", null, $"Microsoft.SemanticKernel.{nameof(ImageContent)}")]
    [InlineData("image/png", "http://localhost:9090", $"Microsoft.SemanticKernel.{nameof(ImageContent)}")]
    public void ToStringShouldReturn(string? mimeType, string? path, string expectedToString)
    {
        // Arrange
        var bytes = Encoding.UTF8.GetBytes("this is a test");
        var data = BinaryData.FromBytes(bytes);
        var content1 = new ImageContent(data, mimeType);
        if (path is not null)
        {
            content1.Uri = new Uri(path);
        }

        // Act
        var result1 = content1.ToString();

        // Assert
        Assert.Equal(expectedToString, result1);
    }

    [Fact]
    public void UpdatingUriPropertyShouldReturnAsExpected()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test");
        var content = new ImageContent(data, "text/plain");

        // Act
        var serializeBefore = JsonSerializer.Serialize(content);

        // Changing the Uri to a absolute file /foo.txt path
        content.Uri = new Uri("file:///foo.txt");
        content.MimeType = "image/jpeg";

        var serializeAfter = JsonSerializer.Serialize(content);

        // Assert
        Assert.Equal("""{"MimeType":"text/plain","Data":"dGhpcyBpcyBhIHRlc3Q="}""", serializeBefore);
        Assert.Equal("""{"Uri":"file:///foo.txt","MimeType":"image/jpeg","Data":"dGhpcyBpcyBhIHRlc3Q="}""", serializeAfter);

        // Uri behaves independently of other properties
        Assert.Equal("file:///foo.txt", content.Uri?.ToString());

        // Data and MimeType remain the same
        Assert.Equal(Convert.FromBase64String("dGhpcyBpcyBhIHRlc3Q="), content.Data!.Value.ToArray());
        Assert.Equal(data.ToArray(), content.Data!.Value.ToArray());
    }

    [Fact]
    public void UpdatingMimeTypePropertyShouldReturnAsExpected()
    {
        // Arrange
        var data = BinaryData.FromString("this is a test");
        var content = new ImageContent(data, "text/plain");

        // Act
        var toStringBefore = content.ToString();

        // Changing the mimetype to image/jpeg in the DataUri
        Assert.Equal("data:text/plain;base64,dGhpcyBpcyBhIHRlc3Q=", content.DataUri);

        content.MimeType = "application/json";
        Assert.Equal("data:application/json;base64,dGhpcyBpcyBhIHRlc3Q=", content.DataUri);
        Assert.Null(content.Uri); // Uri behaves independently of other properties, was not set, keeps null.
        Assert.Equal(Convert.FromBase64String("dGhpcyBpcyBhIHRlc3Q="), content.Data!.Value.ToArray());
        Assert.Equal(data.ToArray(), content.Data!.Value.ToArray());
        Assert.Equal("application/json", content.MimeType);
    }

    [Fact]
    public void UpdateDataPropertyShouldReturnAsExpected()
    {
        // Arrange
        var dataUriBefore = "data:text/plain;base64,dGhpcyBpcyBhIHRlc3Q=";
        var content = new ImageContent(dataUriBefore);

        // Act
        var newData = BinaryData.FromString("this is a new test");
        dataUriBefore = content.DataUri!;
        content.Data = newData;

        // Assert
        Assert.Equal("data:text/plain;base64,dGhpcyBpcyBhIHRlc3Q=", dataUriBefore);
        Assert.Equal("data:text/plain;base64,dGhpcyBpcyBhIG5ldyB0ZXN0", content.DataUri);
        Assert.Null(content.Uri); // Uri behaves independently of other properties, was not set, keeps null.
        Assert.Equal("text/plain", content.MimeType); // MimeType remain the same as it was not set
        Assert.Equal(Convert.FromBase64String("dGhpcyBpcyBhIG5ldyB0ZXN0"), content.Data!.Value.ToArray()); // Data is updated
    }

    [Fact]
    public void EmptyConstructorSerializationAndDeserializationAsExpected()
    {
        var content = new ImageContent();
        var serialized = JsonSerializer.Serialize(content);
        var deserialized = JsonSerializer.Deserialize<ImageContent>(serialized);

        Assert.Equal("{}", serialized);

        Assert.NotNull(deserialized);
        Assert.Null(deserialized.Uri);
        Assert.Null(deserialized.Data);
        Assert.Null(deserialized.MimeType);
        Assert.Null(deserialized.InnerContent);
        Assert.Null(deserialized.ModelId);
        Assert.Null(deserialized.Metadata);
    }

    [Fact]
    public void MetadataSerializationAndDeserializationWorksCorrectly()
    {
        // Arrange
        var content = new ImageContent()
        {
            Metadata = new Dictionary<string, object?> { ["ChatImageDetailLevel"] = "high" }
        };

        // Act
        var serialized = JsonSerializer.Serialize(content);
        var deserialized = JsonSerializer.Deserialize<ImageContent>(serialized);

        // Assert
        Assert.NotNull(deserialized?.Metadata);
        Assert.True(deserialized.Metadata.ContainsKey("ChatImageDetailLevel"));
        Assert.Equal("high", deserialized.Metadata["ChatImageDetailLevel"]?.ToString());
    }

    [Theory]
    [InlineData("http://localhost:9090/")]
    [InlineData(null)]
    public void UriConstructorSerializationAndDeserializationAsExpected(string? path)
    {
#pragma warning disable CS8600 // Converting null literal or possible null value to non-nullable type.
#pragma warning disable CS8604 // Possible null reference argument.
        Uri uri = path is not null ? new Uri(path) : null;

        var content = new ImageContent(uri);
        var serialized = JsonSerializer.Serialize(content);
        var deserialized = JsonSerializer.Deserialize<ImageContent>(serialized);

        if (uri is null)
        {
            Assert.Equal("{}", serialized);
        }
        else
        {
            Assert.Equal($"{{\"Uri\":\"{uri}\"}}", serialized);
        }

        Assert.NotNull(deserialized);
        Assert.Equal(uri, deserialized.Uri);
        Assert.Null(deserialized.Data);
        Assert.Null(deserialized.MimeType);
        Assert.Null(deserialized.InnerContent);
        Assert.Null(deserialized.ModelId);
        Assert.Null(deserialized.Metadata);
#pragma warning restore CS8604 // Possible null reference argument.
#pragma warning restore CS8600 // Converting null literal or possible null value to non-nullable type.
    }
}
