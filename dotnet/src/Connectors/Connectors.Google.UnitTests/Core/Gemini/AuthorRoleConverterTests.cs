// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Buffers;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Google.Core;
using Xunit;

namespace SemanticKernel.Connectors.Google.UnitTests.Core.Gemini;

public sealed class AuthorRoleConverterTests
{
    [Fact]
    public void ReadWhenRoleIsUserReturnsUser()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var reader = new Utf8JsonReader("\"user\""u8);

        // Act
        reader.Read();
        var result = converter.Read(ref reader, typeof(AuthorRole?), JsonSerializerOptions.Default);

        // Assert
        Assert.Equal(AuthorRole.User, result);
    }

    [Fact]
    public void ReadWhenRoleIsModelReturnsAssistant()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var reader = new Utf8JsonReader("\"model\""u8);

        // Act
        reader.Read();
        var result = converter.Read(ref reader, typeof(AuthorRole?), JsonSerializerOptions.Default);

        // Assert
        Assert.Equal(AuthorRole.Assistant, result);
    }

    [Fact]
    public void ReadWhenRoleIsFunctionReturnsTool()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var reader = new Utf8JsonReader("\"function\""u8);

        // Act
        reader.Read();
        var result = converter.Read(ref reader, typeof(AuthorRole?), JsonSerializerOptions.Default);

        // Assert
        Assert.Equal(AuthorRole.Tool, result);
    }

    [Fact]
    public void ReadWhenRoleIsNullReturnsNull()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var reader = new Utf8JsonReader("null"u8);

        // Act
        reader.Read();
        var result = converter.Read(ref reader, typeof(AuthorRole?), JsonSerializerOptions.Default);

        // Assert
        Assert.Null(result);
    }

    [Fact]
    public void ReadWhenRoleIsUnknownThrows()
    {
        // Arrange
        var converter = new AuthorRoleConverter();

        // Act
        void Act()
        {
            var reader = new Utf8JsonReader("\"unknown\""u8);
            reader.Read();
            converter.Read(ref reader, typeof(AuthorRole?), JsonSerializerOptions.Default);
        }

        // Assert
        Assert.Throws<JsonException>(Act);
    }

    [Fact]
    public void WriteWhenRoleIsUserReturnsUser()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var bufferWriter = new ArrayBufferWriter<byte>();
        using var writer = new Utf8JsonWriter(bufferWriter);

        // Act
        converter.Write(writer, AuthorRole.User, JsonSerializerOptions.Default);

        // Assert
        Assert.Equal("\"user\""u8, bufferWriter.GetSpan().Trim((byte)'\0'));
    }

    [Fact]
    public void WriteWhenRoleIsAssistantReturnsModel()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var bufferWriter = new ArrayBufferWriter<byte>();
        using var writer = new Utf8JsonWriter(bufferWriter);

        // Act
        converter.Write(writer, AuthorRole.Assistant, JsonSerializerOptions.Default);

        // Assert
        Assert.Equal("\"model\""u8, bufferWriter.GetSpan().Trim((byte)'\0'));
    }

    [Fact]
    public void WriteWhenRoleIsToolReturnsFunction()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var bufferWriter = new ArrayBufferWriter<byte>();
        using var writer = new Utf8JsonWriter(bufferWriter);

        // Act
        converter.Write(writer, AuthorRole.Tool, JsonSerializerOptions.Default);

        // Assert
        Assert.Equal("\"function\""u8, bufferWriter.GetSpan().Trim((byte)'\0'));
    }

    [Fact]
    public void WriteWhenRoleIsNullReturnsNull()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        var bufferWriter = new ArrayBufferWriter<byte>();
        using var writer = new Utf8JsonWriter(bufferWriter);

        // Act
        converter.Write(writer, null, JsonSerializerOptions.Default);

        // Assert
        Assert.Equal("null"u8, bufferWriter.GetSpan().Trim((byte)'\0'));
    }

    [Fact]
    public void WriteWhenRoleIsNotUserOrAssistantOrToolThrows()
    {
        // Arrange
        var converter = new AuthorRoleConverter();
        using var writer = new Utf8JsonWriter(new ArrayBufferWriter<byte>());

        // Act
        void Act()
        {
            converter.Write(writer, AuthorRole.System, JsonSerializerOptions.Default);
        }

        // Assert
        Assert.Throws<JsonException>(Act);
    }
}
