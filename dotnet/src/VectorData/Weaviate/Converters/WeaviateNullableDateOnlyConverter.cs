// Copyright (c) Microsoft. All rights reserved.

#if NET

using System;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Converts nullable <see cref="DateOnly"/> to RFC 3339 formatted string for Weaviate.
/// DateOnly values are stored as midnight UTC.
/// </summary>
internal sealed class WeaviateNullableDateOnlyConverter : JsonConverter<DateOnly?>
{
    private const string DateTimeFormat = "yyyy-MM-dd'T'HH:mm:ss.fffZ";

    public override DateOnly? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var dateString = reader.GetString();

        if (string.IsNullOrWhiteSpace(dateString))
        {
            return null;
        }

        var dateTimeOffset = DateTimeOffset.Parse(dateString, CultureInfo.InvariantCulture);
        return DateOnly.FromDateTime(dateTimeOffset.DateTime);
    }

    public override void Write(Utf8JsonWriter writer, DateOnly? value, JsonSerializerOptions options)
    {
        if (value.HasValue)
        {
            var dateTimeOffset = new DateTimeOffset(value.Value.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);
            writer.WriteStringValue(dateTimeOffset.ToString(DateTimeFormat, CultureInfo.InvariantCulture));
        }
        else
        {
            writer.WriteNullValue();
        }
    }
}

#endif
