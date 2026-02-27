// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Converts nullable <see cref="DateTime"/> to RFC 3339 formatted string for Weaviate.
/// </summary>
internal sealed class WeaviateNullableDateTimeConverter : JsonConverter<DateTime?>
{
    private const string DateTimeFormat = "yyyy-MM-dd'T'HH:mm:ss.fffK";

    public override DateTime? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var dateString = reader.GetString();

        if (string.IsNullOrWhiteSpace(dateString))
        {
            return null;
        }

        // Parse as DateTimeOffset to properly handle timezone, then convert to UTC DateTime.
        // Weaviate may return the timestamp in a different timezone than it was stored in.
        return DateTimeOffset.Parse(dateString, CultureInfo.InvariantCulture).UtcDateTime;
    }

    public override void Write(Utf8JsonWriter writer, DateTime? value, JsonSerializerOptions options)
    {
        if (value.HasValue)
        {
            // When DateTime.Kind is Unspecified, the 'K' format specifier produces an empty string (no timezone),
            // which violates RFC 3339. Treat Unspecified as UTC so 'K' produces 'Z'.
            var v = value.Value;
            if (v.Kind == DateTimeKind.Unspecified)
            {
                v = DateTime.SpecifyKind(v, DateTimeKind.Utc);
            }

            writer.WriteStringValue(v.ToString(DateTimeFormat, CultureInfo.InvariantCulture));
        }
        else
        {
            writer.WriteNullValue();
        }
    }
}
