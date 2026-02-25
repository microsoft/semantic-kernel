// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.CosmosNoSql;

/// <summary>
/// A JSON converter for byte arrays that serializes them as JSON arrays of numbers
/// instead of base64-encoded strings.
/// </summary>
/// <remarks>
/// This is needed because Cosmos DB's VectorDistance function requires vectors to be arrays of numbers,
/// not base64-encoded strings.
/// </remarks>
internal sealed class ByteArrayJsonConverter : JsonConverter<byte[]>
{
    /// <inheritdoc/>
    public override byte[] Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        // Support reading both base64 strings (for backward compatibility) and number arrays
        if (reader.TokenType == JsonTokenType.String)
        {
            return reader.GetBytesFromBase64();
        }

        if (reader.TokenType != JsonTokenType.StartArray)
        {
            throw new JsonException($"Expected StartArray or String token, got {reader.TokenType}");
        }

        var list = new List<byte>();
        while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
        {
            list.Add(reader.GetByte());
        }
        return list.ToArray();
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, byte[] value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();
        foreach (var b in value)
        {
            writer.WriteNumberValue(b);
        }
        writer.WriteEndArray();
    }
}

/// <summary>
/// A JSON converter for <see cref="ReadOnlyMemory{T}"/> of byte that serializes as JSON arrays of numbers
/// instead of base64-encoded strings.
/// </summary>
/// <remarks>
/// This is needed because Cosmos DB's VectorDistance function requires vectors to be arrays of numbers,
/// not base64-encoded strings.
/// </remarks>
internal sealed class ReadOnlyMemoryByteJsonConverter : JsonConverter<ReadOnlyMemory<byte>>
{
    /// <inheritdoc/>
    public override ReadOnlyMemory<byte> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        // Support reading both base64 strings (for backward compatibility) and number arrays
        if (reader.TokenType == JsonTokenType.String)
        {
            return new ReadOnlyMemory<byte>(reader.GetBytesFromBase64());
        }

        if (reader.TokenType != JsonTokenType.StartArray)
        {
            throw new JsonException($"Expected StartArray or String token, got {reader.TokenType}");
        }

        var list = new List<byte>();
        while (reader.Read() && reader.TokenType != JsonTokenType.EndArray)
        {
            list.Add(reader.GetByte());
        }
        return new ReadOnlyMemory<byte>(list.ToArray());
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, ReadOnlyMemory<byte> value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();
        foreach (var b in value.Span)
        {
            writer.WriteNumberValue(b);
        }
        writer.WriteEndArray();
    }
}
