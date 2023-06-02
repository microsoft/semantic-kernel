// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Qdrant.Http.ApiSchema;
#pragma warning disable CA1812 // Avoid uninstantiated internal classes: Used for Json Deserialization
internal sealed class NumberToStringConverter : JsonConverter<string>
{
    public override string Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (typeToConvert != typeof(string))
        {
            throw new NotSupportedException($"{nameof(typeToConvert)}: {typeToConvert}");
        }

        switch (reader.TokenType)
        {
            case JsonTokenType.String:
                return reader.GetString()!;
            case JsonTokenType.Number:
                if (reader.TryGetInt32(out var valueInt))
                {
                    return valueInt.ToString("D", NumberFormatInfo.InvariantInfo);
                }

                throw new NotSupportedException("Invalid integer specified.");
            default:
                throw new NotSupportedException($"{nameof(JsonTokenType)}.{reader.TokenType}");
        }
    }

    public override void Write(Utf8JsonWriter writer, string @value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(@value);
    }
}
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
