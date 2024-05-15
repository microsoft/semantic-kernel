// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

public sealed class BinaryContentTests
{
    [Fact]
    public void ItCanBeSerialized()
    {
        Assert.Equal("{}",
            JsonSerializer.Serialize(new BinaryContent()));

        Assert.Equal("{}",
            JsonSerializer.Serialize(new BinaryContent(dataUri: null)));

        Assert.Equal("""{"mimeType":"application/octet-stream","data":"AQIDBA=="}""",
            JsonSerializer.Serialize(new BinaryContent(
                dataUri: "data:application/octet-stream;base64,AQIDBA==")));

        Assert.Equal("""{"mimeType":"application/octet-stream","data":"AQIDBA=="}""",
            JsonSerializer.Serialize(new BinaryContent(
                data: new ReadOnlyMemory<byte>([0x01, 0x02, 0x03, 0x04]),
                mimeType: "application/octet-stream")
            ));
    }

    [Fact]
    public void ItCanBeDeserialized()
    {
        // Empty Binary Object
        var content = JsonSerializer.Deserialize<BinaryContent>("{}")!;
        Assert.Null(content.Data);
        Assert.Null(content.DataUri);
        Assert.Null(content.MimeType);
        Assert.Null(content.Uri);
        Assert.False(content.CanRead());

        // Data + MimeType only
        content = JsonSerializer.Deserialize<BinaryContent>("""{"mimeType":"application/octet-stream","data":"AQIDBA=="}""")!;

        Assert.Null(content.Uri);
        Assert.NotNull(content.Data);
        Assert.Equal(new ReadOnlyMemory<byte>([0x01, 0x02, 0x03, 0x04]), content.Data!.Value);
        Assert.Equal("application/octet-stream", content.MimeType);
        Assert.True(content.CanRead());

        // Uri referenced content-only 
        content = JsonSerializer.Deserialize<BinaryContent>("""{"mimeType":"application/octet-stream","uri":"http://localhost/"}""")!;

        Assert.Null(content.Data);
        Assert.Null(content.DataUri);
        Assert.Equal("application/octet-stream", content.MimeType);
        Assert.Equal(new Uri("http://localhost/"), content.Uri);
        Assert.False(content.CanRead());

        // Using extra metadata
        content = JsonSerializer.Deserialize<BinaryContent>("""
            {
                "data": "AQIDBA==",
                "modelId": "gpt-4",
                "metadata": {
                    "key": "value"
                },
                "uri": "http://localhost/myfile.txt",
                "mimeType": "text/plain"
            }
        """)!;

        Assert.Equal(new Uri("http://localhost/myfile.txt"), content.Uri);
        Assert.NotNull(content.Data);
        Assert.Equal(new ReadOnlyMemory<byte>([0x01, 0x02, 0x03, 0x04]), content.Data!.Value);
        Assert.Equal("text/plain", content.MimeType);
        Assert.True(content.CanRead());
        Assert.Equal("gpt-4", content.ModelId);
        Assert.Equal("value", content.Metadata!["key"]!.ToString());
    }

    [Fact]
    public void ItCanBecomeReadableAfterProvidingDataUri()
    {
        var content = new BinaryContent(new Uri("http://localhost/"));
        Assert.False(content.CanRead());
        Assert.Equal("http://localhost/", content.Uri?.ToString());
        Assert.Null(content.MimeType);

        content.DataUri = "data:text/plain;base64,VGhpcyBpcyBhIHRleHQgY29udGVudA==";
        Assert.True(content.CanRead());
        Assert.Equal("text/plain", content.MimeType);
        Assert.Equal("http://localhost/", content.Uri!.ToString());
        Assert.Equal(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA=="), content.Data!.Value.ToArray());
    }

    [Fact]
    public void ItCanBecomeReadableAfterProvidingData()
    {
        var content = new BinaryContent(new Uri("http://localhost/"));
        Assert.False(content.CanRead());
        Assert.Equal("http://localhost/", content.Uri?.ToString());
        Assert.Null(content.MimeType);

        content.Data = new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA=="));
        Assert.True(content.CanRead());
        Assert.Null(content.MimeType);
        Assert.Equal("http://localhost/", content.Uri!.ToString());
        Assert.Equal(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA=="), content.Data!.Value.ToArray());
    }

    [Fact]
    public void ItBecomesUnreadableAfterRemovingData()
    {
        var content = new BinaryContent(data: new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA==")), mimeType: "text/plain");
        Assert.True(content.CanRead());

        content.Data = null;
        Assert.False(content.CanRead());
        Assert.Null(content.DataUri);
    }

    [Fact]
    public void ItBecomesUnreadableAfterRemovingDataUri()
    {
        var content = new BinaryContent(data: new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA==")), mimeType: "text/plain");
        Assert.True(content.CanRead());

        content.DataUri = null;
        Assert.False(content.CanRead());
        Assert.Null(content.DataUri);
    }

    [Theory]
    [InlineData("http://localhost/")]
    [InlineData("about:blank")]
    [InlineData("file://c:\\temp")]
    [InlineData("")]
    [InlineData("invalid")]
    public void DataUriConstructorShouldThrowWhenInvalidDataUriIsProvided(string invalidData)
    {
        Assert.Throws<ArgumentException>(() => new BinaryContent(dataUri: invalidData));
    }

    [Fact]
    public void GetDataUriWithoutMimeTypeShouldThrow()
    {
        // Arrange
        var content = new BinaryContent
        {
            Data = new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA=="))
        };

        // Act & Assert
        Assert.Throws<InvalidOperationException>(() => content.DataUri);
    }

    [Fact]
    public void WhenProvidingDataUriToAnAlreadyExistingDataItOverridesAsExpected()
    {
        // Arrange
        var content = new BinaryContent(
            data: new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA==")),
            mimeType: "text/plain",
            uri: new Uri("http://localhost/"));

        // Act
        content.DataUri = "data:image/jpeg;base64,AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=";

        // Assert
        Assert.Equal("image/jpeg", content.MimeType);
        Assert.Equal("data:image/jpeg;base64,AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", content.DataUri);
        Assert.NotNull(content.Data);
        Assert.Equal(Convert.FromBase64String("AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="), content.Data!.Value.ToArray());

        // Don't change the referred Uri
        Assert.Equal("http://localhost/", content.Uri?.ToString());
    }
}
