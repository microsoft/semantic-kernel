// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Serialization;
using System.Text.Json;
using System.Globalization;

namespace Microsoft.SemanticKernel.Functions;
internal class CultureInfoJsonConverter : JsonConverter<CultureInfo>
{
    public override CultureInfo? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        return reader.TokenType switch
        {
            JsonTokenType.String => new CultureInfo(reader.GetString()!),
            _ => throw new NotSupportedException($"{nameof(JsonTokenType)}.{reader.TokenType}"),
        };
    }

    public override void Write(Utf8JsonWriter writer, CultureInfo value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value.Name);
    }
}
