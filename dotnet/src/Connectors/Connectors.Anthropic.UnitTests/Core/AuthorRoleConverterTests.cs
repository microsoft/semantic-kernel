// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Buffers;
using System.Text.Json;
using Microsoft.SemanticKernel.ChatCompletion;
using Microsoft.SemanticKernel.Connectors.Anthropic.Core;
using Xunit;

namespace SemanticKernel.Connectors.Anthropic.UnitTests.Core;

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
        var reader = new Utf8JsonReader("\"assistant\""u8);

        // Act
        reader.Read();
        var result = converter.Read(ref reader, typeof(AuthorRole?), JsonSerializerOptions.Default);

        // Assert
        Assert.Equal(AuthorRole.Assistant, result);
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
        Assert.Equal("\"assistant\""u8, bufferWriter.GetSpan().Trim((byte)'\0'));
    }

    [Fact]
    public void WriteWhenRoleIsNotUserOrAssistantThrows()
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
