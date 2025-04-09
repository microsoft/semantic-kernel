// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using Microsoft.SemanticKernel;
using Xunit;
using Xunit.Abstractions;

namespace SemanticKernel.UnitTests.Contents;

public sealed class BinaryContentTests(ITestOutputHelper output)
{
    [Fact]
    public void ItCanBeSerialized()
    {
        Assert.Equal("{}",
            JsonSerializer.Serialize(new BinaryContent()));

        Assert.Equal("""{"MimeType":"text/plain","Data":""}""",
            JsonSerializer.Serialize(new BinaryContent("data:,")));

        Assert.Equal("""{"Uri":"http://localhost/"}""",
            JsonSerializer.Serialize(new BinaryContent(new Uri("http://localhost/"))));

        Assert.Equal("""{"MimeType":"application/octet-stream","Data":"AQIDBA=="}""",
            JsonSerializer.Serialize(new BinaryContent(
                dataUri: "data:application/octet-stream;base64,AQIDBA==")));

        Assert.Equal("""{"MimeType":"application/octet-stream","Data":"AQIDBA=="}""",
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
        content = JsonSerializer.Deserialize<BinaryContent>("""{"MimeType":"application/octet-stream","Data":"AQIDBA=="}""")!;

        Assert.Null(content.Uri);
        Assert.NotNull(content.Data);
        Assert.Equal(new ReadOnlyMemory<byte>([0x01, 0x02, 0x03, 0x04]), content.Data!.Value);
        Assert.Equal("application/octet-stream", content.MimeType);
        Assert.True(content.CanRead);

        // Uri referenced content-only 
        content = JsonSerializer.Deserialize<BinaryContent>("""{"MimeType":"application/octet-stream","Uri":"http://localhost/"}""")!;

        Assert.Null(content.Data);
        Assert.Null(content.DataUri);
        Assert.Equal("application/octet-stream", content.MimeType);
        Assert.Equal(new Uri("http://localhost/"), content.Uri);
        Assert.False(content.CanRead);

        // Using extra metadata
        content = JsonSerializer.Deserialize<BinaryContent>("""
            {
                "Data": "AQIDBA==",
                "ModelId": "gpt-4",
                "Metadata": {
                    "key": "value"
                },
                "Uri": "http://localhost/myfile.txt",
                "MimeType": "text/plain"
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
        """{"Data": "AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", "MimeType": "text/plain" }""",
        """{"MimeType":"text/plain","Data":"AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8="}""")]
    [InlineData( // Does not support non-readable content
        """{"DataUri": "data:text/plain;base64,AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", "unexpected": true }""",
        "{}")]
    [InlineData( // Only serializes the read/writeable properties
        """{"DataUri": "data:text/plain;base64,AAECAwQFBgcICQoLDA0ODxAREhMUFRYXGBkaGxwdHh8=", "MimeType": "text/plain" }""",
        """{"MimeType":"text/plain"}""")]
    [InlineData( // Uri comes before mimetype
        """{"MimeType": "text/plain", "Uri": "http://localhost/" }""",
        """{"Uri":"http://localhost/","MimeType":"text/plain"}""")]
    public void DeserializationAndSerializationBehaveAsExpected(string serialized, string expectedToString)
    {
        // Arrange
        var content = JsonSerializer.Deserialize<BinaryContent>(serialized)!;

        // Act & Assert
        var reSerialization = JsonSerializer.Serialize(content);

        Assert.Equal(expectedToString, reSerialization);
    }

    [Theory]
    // Other formats
    [InlineData("http://localhost/", typeof(UriFormatException))]
    [InlineData("about:blank", typeof(UriFormatException))]
    [InlineData("file://c:\\temp", typeof(UriFormatException))]
    [InlineData("invalid", typeof(UriFormatException))]

    // Data format validation errors
    [InlineData("", typeof(UriFormatException))] // Empty data uri
    [InlineData("data", typeof(UriFormatException))] // data missing colon
    [InlineData("data:", typeof(UriFormatException))] // data missing comma
    [InlineData("data:something,", typeof(UriFormatException))] // mime type without subtype
    [InlineData("data:something;else,data", typeof(UriFormatException))] // mime type without subtype
    [InlineData("data:type/subtype;parameterwithoutvalue;else,", typeof(UriFormatException))] // parameter without value
    [InlineData("data:type/subtype;;parameter=value;else,", typeof(UriFormatException))] // parameter without value
    [InlineData("data:type/subtype;parameter=va=lue;else,", typeof(UriFormatException))] // parameter with multiple = 
    [InlineData("data:type/subtype;=value;else,", typeof(UriFormatException))] // empty parameter name

    // Base64 Validation Errors
    [InlineData("data:text;base64,something!", typeof(UriFormatException))]  // Invalid base64 due to invalid character '!'
    [InlineData("data:text/plain;base64,U29tZQ==\t", typeof(UriFormatException))] // Invalid base64 due to tab character
    [InlineData("data:text/plain;base64,U29tZQ==\r", typeof(UriFormatException))] // Invalid base64 due to carriage return character
    [InlineData("data:text/plain;base64,U29tZQ==\n", typeof(UriFormatException))] // Invalid base64 due to line feed character
    [InlineData("data:text/plain;base64,U29t\r\nZQ==", typeof(UriFormatException))] // Invalid base64 due to carriage return and line feed characters
    [InlineData("data:text/plain;base64,U29", typeof(UriFormatException))] // Invalid base64 due to missing padding
    [InlineData("data:text/plain;base64,U29tZQ", typeof(UriFormatException))] // Invalid base64 due to missing padding
    [InlineData("data:text/plain;base64,U29tZQ=", typeof(UriFormatException))] // Invalid base64 due to missing padding
    public void ItThrowsOnInvalidDataUri(string path, Type exception)
    {
        var thrownException = Assert.Throws(exception, () => new BinaryContent(path));
        output.WriteLine(thrownException.Message);
    }

    [Theory]
    [InlineData("data:;parameter1=value1,", "{}", """{"data-uri-parameter1":"value1"}""")] // Should create extra data
    [InlineData("data:;parameter1=value1,", """{"Metadata":{"data-uri-parameter1":"should override me"}}""", """{"data-uri-parameter1":"value1"}""")] // Should override existing data
    [InlineData("data:;parameter1=value1,", """{"Metadata":{"data-uri-parameter2":"value2"}}""", """{"data-uri-parameter1":"value1","data-uri-parameter2":"value2"}""")] // Should merge existing data with new data
    [InlineData("data:;parameter1=value1;parameter2=value2,data", """{"Metadata":{"data-uri-parameter2":"should override me"}}""", """{"data-uri-parameter1":"value1","data-uri-parameter2":"value2"}""")] // Should merge existing data with new data
    [InlineData("data:image/jpeg;parameter1=value1;parameter2=value2;base64,data", """{"Metadata":{"data-uri-parameter2":"should override me"}}""", """{"data-uri-parameter1":"value1","data-uri-parameter2":"value2"}""")] // Should merge existing data with new data
    [InlineData("data:image/jpeg;parameter1=value1;parameter2=value2;base64,data", """{"Metadata":{"data-uri-parameter3":"existing data", "data-uri-parameter2":"should override me"}}""", """{"data-uri-parameter1":"value1","data-uri-parameter2":"value2","data-uri-parameter3":"existing data"}""")] // Should keep previous metadata
    public void DataUriConstructorWhenProvidingParametersUpdatesMetadataAsExpected(string path, string startingSerializedBinaryContent, string expectedSerializedMetadata)
    {
        // Arrange
        var content = JsonSerializer.Deserialize<BinaryContent>(startingSerializedBinaryContent)!;
        content.DataUri = path;

        var expectedMetadata = JsonSerializer.Deserialize<Dictionary<string, object?>>(expectedSerializedMetadata)!;

        // Act & Assert
        Assert.Equal(expectedMetadata.Count, content.Metadata!.Count);
        foreach (var kvp in expectedMetadata)
        {
            Assert.True(content.Metadata.ContainsKey(kvp.Key));
            Assert.Equal(kvp.Value?.ToString(), content.Metadata[kvp.Key]?.ToString());
        }
    }

    [Fact]
    public void ItPreservePreviousMetadataForParameterizedDataUri()
    {
        // Arrange
        var content = new BinaryContent
        {
            Metadata = new Dictionary<string, object?>
            {
                { "key1", "value1" },
                { "key2", "value2" }
            }
        };

        // Act
        content.DataUri = "data:;parameter1=parametervalue1;parameter2=parametervalue2;base64,data";

        // Assert
        Assert.Equal(4, content.Metadata!.Count);
        Assert.Equal("value1", content.Metadata["key1"]?.ToString());
        Assert.Equal("value2", content.Metadata["key2"]?.ToString());
        Assert.Equal("parametervalue1", content.Metadata["data-uri-parameter1"]?.ToString());
        Assert.Equal("parametervalue2", content.Metadata["data-uri-parameter2"]?.ToString());
    }

    [Fact]
    public void DeserializesParameterizedDataUriAsExpected()
    {
        // Arrange
        var content = new BinaryContent
        {
            Data = new ReadOnlyMemory<byte>(Convert.FromBase64String("U29tZSBkYXRh")),
            MimeType = "application/json",
            Metadata = new Dictionary<string, object?>
            {
                { "data-uri-parameter1", "value1" },
                { "data-uri-parameter2", "value2" }
            }
        };

        var expectedDataUri = "data:application/json;parameter1=value1;parameter2=value2;base64,U29tZSBkYXRh";

        // Act & Assert
        Assert.Equal(expectedDataUri, content.DataUri);
    }

    [Theory]
    [InlineData("data:application/octet-stream;utf8,01-02-03-04")]
    [InlineData("data:application/json,01-02-03-04")]
    [InlineData("data:,01-02-03-04")]
    public void ReturnUTF8EncodedWhenDataIsNotBase64(string path)
    {
        // Arrange
        var content = new BinaryContent(path);

        // Act & Assert
        Assert.Equal("01-02-03-04", Encoding.UTF8.GetString(content.Data!.Value.ToArray()));
    }
}
