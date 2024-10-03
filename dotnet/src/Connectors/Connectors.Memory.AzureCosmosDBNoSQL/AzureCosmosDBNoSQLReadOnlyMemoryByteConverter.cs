// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;

/// <summary>
/// Contains serialization and deserialization logic for <see cref="ReadOnlyMemory{T}"/> of <see cref="byte"/>
/// to avoid default base64 encoding/decoding.
/// </summary>
internal sealed class AzureCosmosDBNoSQLReadOnlyMemoryByteConverter : JsonConverter<ReadOnlyMemory<byte>>
{
    public override ReadOnlyMemory<byte> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartArray)
        {
            throw new JsonException("Expected StartArray token when deserializing ReadOnlyMemory<byte>.");
        }

        var byteList = new List<byte>();

        while (reader.Read())
        {
            if (reader.TokenType == JsonTokenType.EndArray)
            {
                break;
            }

            if (reader.TokenType != JsonTokenType.Number)
            {
                throw new JsonException("Expected byte values in the array.");
            }

            byteList.Add(reader.GetByte());
        }

        return new ReadOnlyMemory<byte>(byteList.ToArray());
    }

    public override void Write(Utf8JsonWriter writer, ReadOnlyMemory<byte> value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();

        foreach (var b in value.ToArray())
        {
            writer.WriteNumberValue(b);
        }

        writer.WriteEndArray();
    }
}
