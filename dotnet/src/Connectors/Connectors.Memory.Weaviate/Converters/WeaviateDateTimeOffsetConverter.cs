// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Converts datetime type to RFC 3339 formatted string.
/// </summary>
internal sealed class WeaviateDateTimeOffsetConverter : JsonConverter<DateTimeOffset>
{
    private const string DateTimeFormat = "yyyy-MM-dd'T'HH:mm:ss.fffK";

    public override DateTimeOffset Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var dateString = reader.GetString();

        if (string.IsNullOrWhiteSpace(dateString))
        {
            return default;
        }

        return DateTimeOffset.Parse(dateString, CultureInfo.InvariantCulture);
    }

    public override void Write(Utf8JsonWriter writer, DateTimeOffset value, JsonSerializerOptions options)
    {
        writer.WriteStringValue(value.ToString(DateTimeFormat, CultureInfo.InvariantCulture));
    }
}
