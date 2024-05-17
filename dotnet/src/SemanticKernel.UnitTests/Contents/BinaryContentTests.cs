// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Text;
using Xunit;

namespace SemanticKernel.UnitTests.Contents;

public sealed class BinaryContentTests(ITestOutputHelper output)
{
    [Fact]
    public void ItCanBeSerialized()
    {
        Assert.Equal("{}",
            JsonSerializer.Serialize(new BinaryContent()));

        Assert.Equal("{}",
            JsonSerializer.Serialize(new BinaryContent(dataUri: null)));

        Assert.Equal("{}",
            JsonSerializer.Serialize(new BinaryContent(uri: null)));

        Assert.Equal("""{"uri":"http://localhost/"}""",
            JsonSerializer.Serialize(new BinaryContent(new Uri("http://localhost/"))));

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
        Assert.False(content.CanRead);

        // Data + MimeType only
        content = JsonSerializer.Deserialize<BinaryContent>("""{"mimeType":"application/octet-stream","data":"AQIDBA=="}""")!;

        Assert.Null(content.Uri);
        Assert.NotNull(content.Data);
        Assert.Equal(new ReadOnlyMemory<byte>([0x01, 0x02, 0x03, 0x04]), content.Data!.Value);
        Assert.Equal("application/octet-stream", content.MimeType);
        Assert.True(content.CanRead);

        // Uri referenced content-only 
        content = JsonSerializer.Deserialize<BinaryContent>("""{"mimeType":"application/octet-stream","uri":"http://localhost/"}""")!;

        Assert.Null(content.Data);
        Assert.Null(content.DataUri);
        Assert.Equal("application/octet-stream", content.MimeType);
        Assert.Equal(new Uri("http://localhost/"), content.Uri);
        Assert.False(content.CanRead);

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
        Assert.True(content.CanRead);
        Assert.Equal("gpt-4", content.ModelId);
        Assert.Equal("value", content.Metadata!["key"]!.ToString());
    }

    [Fact]
    public void ItCanBecomeReadableAfterProvidingDataUri()
    {
        var content = new BinaryContent(new Uri("http://localhost/"));
        Assert.False(content.CanRead);
        Assert.Equal("http://localhost/", content.Uri?.ToString());
        Assert.Null(content.MimeType);

        content.DataUri = "data:text/plain;base64,VGhpcyBpcyBhIHRleHQgY29udGVudA==";
        Assert.True(content.CanRead);
        Assert.Equal("text/plain", content.MimeType);
        Assert.Equal("http://localhost/", content.Uri!.ToString());
        Assert.Equal(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA=="), content.Data!.Value.ToArray());
    }

    [Fact]
    public void ItCanBecomeReadableAfterProvidingData()
    {
        var content = new BinaryContent(new Uri("http://localhost/"));
        Assert.False(content.CanRead);
        Assert.Equal("http://localhost/", content.Uri?.ToString());
        Assert.Null(content.MimeType);

        content.Data = new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA=="));
        Assert.True(content.CanRead);
        Assert.Null(content.MimeType);
        Assert.Equal("http://localhost/", content.Uri!.ToString());
        Assert.Equal(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA=="), content.Data!.Value.ToArray());
    }

    [Fact]
    public void ItBecomesUnreadableAfterRemovingData()
    {
        var content = new BinaryContent(data: new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA==")), mimeType: "text/plain");
        Assert.True(content.CanRead);

        content.Data = null;
        Assert.False(content.CanRead);
        Assert.Null(content.DataUri);
    }

    [Fact]
    public void ItBecomesUnreadableAfterRemovingDataUri()
    {
        var content = new BinaryContent(data: new ReadOnlyMemory<byte>(Convert.FromBase64String("VGhpcyBpcyBhIHRleHQgY29udGVudA==")), mimeType: "text/plain");
        Assert.True(content.CanRead);

        content.DataUri = null;
        Assert.False(content.CanRead);
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
            mimeType: "text/plain")
        { Uri = new Uri("http://localhost/") };

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

    [Theory]
    [InlineData( // Data always comes last in serialization
        """{"data": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", "mimeType": "text/plain" }""",
        """{"mimeType":"text/plain","data":"AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="}""")]
    [InlineData( // Does not support non-readable content
        """{"dataUri": "data:text/plain;base64,AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", "unexpected": true }""",
        "{}")]
    [InlineData( // Only serializes the read/writeable properties
        """{"dataUri": "data:text/plain;base64,AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", "mimeType": "text/plain" }""",
        """{"mimeType":"text/plain"}""")]
    [InlineData( // Uri comes before mimetype
        """{"mimeType": "text/plain", "uri": "http://localhost/" }""",
        """{"uri":"http://localhost/","mimeType":"text/plain"}""")]
    public void DeserializationAndSerializationBehaveAsExpected(string serialized, string expectedToString)
    {
        // Arrange
        var content = JsonSerializer.Deserialize<BinaryContent>(serialized)!;

        // Act & Assert
        var reSerialization = JsonSerializer.Serialize(content);

        Assert.Equal(expectedToString, reSerialization);
    }

    [Theory]
    // Data format validation errors
    [InlineData("", typeof(ArgumentException))] // Empty data uri
    [InlineData("data", typeof(UriFormatException))] // data missing colon
    [InlineData("data:", typeof(UriFormatException))] // data missing comma
    [InlineData("data:something,", typeof(UriFormatException))] // mime type without subtype
    [InlineData("data:something;else,data", typeof(UriFormatException))] // mime type without subtype
    [InlineData("data:type/subtype;parameterwithoutvalue;else,", typeof(UriFormatException))] // parameter without value
    [InlineData("data:type/subtype;;parameter=value;else,", typeof(UriFormatException))] // parameter without value
    // Base64 Validation Errors
    [InlineData("data:text;base64,something!", typeof(UriFormatException))]  // Invalid base64 due to invalid character '!'
    [InlineData("data:text/plain;base64,U29tZQ==\t", typeof(UriFormatException))] // Invalid base64 due to tab character
    [InlineData("data:text/plain;base64,U29tZQ==\r", typeof(UriFormatException))] // Invalid base64 due to carriage return character
    [InlineData("data:text/plain;base64,U29tZQ==\n", typeof(UriFormatException))] // Invalid base64 due to line feed character
    [InlineData("data:text/plain;base64,U29t\r\nZQ==", typeof(UriFormatException))] // Invalid base64 due to carriage return and line feed characters
    [InlineData("data:text/plain;base64,U29", typeof(UriFormatException))] // Invalid base64 due to missing padding
    [InlineData("data:text/plain;base64,U29tZQ", typeof(UriFormatException))] // Invalid base64 due to missing padding
    [InlineData("data:text/plain;base64,U29tZQ=", typeof(UriFormatException))] // Invalid base64 due to missing padding
    public void ItThrowsOnInvalidDataUri(string? path, Type exception)
    {
        var thrownException = Assert.Throws(exception, () => new BinaryContent(path));
        output.WriteLine(thrownException.Message);
    }
}
