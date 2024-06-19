// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using Microsoft.SemanticKernel.Text;
using Xunit;
using Xunit.Abstractions;

#pragma warning disable CA1054 // URI-like parameters should not be strings
#pragma warning disable CA1055 // URI-like parameters should not be strings
#pragma warning disable CA1056 // URI-like parameters should not be strings

namespace SemanticKernel.UnitTests.Utilities;

public class DataUriParserTests(ITestOutputHelper output)
{
    [Theory]
    [InlineData("data:,", "text/plain", "", null, "{}")] // Minimum valid data URI
    [InlineData("data:,A%20brief%20note", "text/plain", "A%20brief%20note", null, "{}")] // Example in RFC 2397 Doc
    [InlineData("data:text/plain;charset=iso-8859-7,%be%fg%be", "text/plain", "%be%fg%be", null, """{"charset":"iso-8859-7"}""")] // Example in RFC 2397 Doc
    [InlineData("""data:image/gif;base64,R0lGODdhMAAwAPAAAAAAAP///ywAAAAAMAAwAAAC8IyPqcvt""", "image/gif", "R0lGODdhMAAwAPAAAAAAAP///ywAAAAAMAAwAAAC8IyPqcvt", "base64", "{}")] // Example in RFC 2397 Doc
    [InlineData("data:text/vnd-example+xyz;foo=bar;base64,R0lGODdh", "text/vnd-example+xyz", "R0lGODdh", "base64", """{"foo":"bar"}""")]
    [InlineData("data:application/octet-stream;base64,AQIDBA==", "application/octet-stream", "AQIDBA==", "base64", "{}")]
    [InlineData("data:text/plain;charset=UTF-8;page=21,the%20data:1234,5678", "text/plain", "the%20data:1234,5678", null, """{"charset":"UTF-8","page":"21"}""")]
    [InlineData("data:image/svg+xml;utf8,<svg width='10'... </svg>", "image/svg+xml", "<svg width='10'... </svg>", "utf8", "{}")]
    [InlineData("data:;charset=UTF-8,the%20data", "text/plain", "the%20data", null, """{"charset":"UTF-8"}""")]
    [InlineData("data:text/vnd-example+xyz;foo=;base64,R0lGODdh", "text/vnd-example+xyz", "R0lGODdh", "base64", """{"foo":""}""")]
    public void ItCanParseDataUri(string dataUri, string? expectedMimeType, string expectedData, string? expectedDataFormat, string serializedExpectedParameters)
    {
        var parsed = DataUriParser.Parse(dataUri);
        var expectedParameters = JsonSerializer.Deserialize<Dictionary<string, string>>(serializedExpectedParameters);

        Assert.Equal(expectedMimeType, parsed.MimeType);
        Assert.Equal(expectedData, parsed.Data);
        Assert.Equal(expectedDataFormat, parsed.DataFormat);
        Assert.Equal(expectedParameters!.Count, parsed.Parameters.Count);
        if (expectedParameters.Count > 0)
        {
            foreach (var kvp in expectedParameters)
            {
                Assert.True(parsed.Parameters.ContainsKey(kvp.Key));
                Assert.Equal(kvp.Value, parsed.Parameters[kvp.Key]);
            }
        }
    }

    [Theory]
    // Data format validation errors
    [InlineData("", typeof(ArgumentException))]
    [InlineData(null, typeof(ArgumentNullException))]
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
    public void ItThrowsOnInvalidDataUri(string? dataUri, Type exception)
    {
        var thrownException = Assert.Throws(exception, () => DataUriParser.Parse(dataUri));
        output.WriteLine(thrownException.Message);
    }
}
