// Copyright (c) Microsoft. All rights reserved.

#if NET

using System;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

/// <summary>
/// Converts <see cref="DateOnly"/> to RFC 3339 formatted string for Weaviate.
/// DateOnly values are stored as midnight UTC.
/// </summary>
internal sealed class WeaviateDateOnlyConverter : JsonConverter<DateOnly>
{
    private const string DateTimeFormat = "yyyy-MM-dd'T'HH:mm:ss.fffZ";

    public override DateOnly Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var dateString = reader.GetString();

        if (string.IsNullOrWhiteSpace(dateString))
        {
            return default;
        }

        var dateTimeOffset = DateTimeOffset.Parse(dateString, CultureInfo.InvariantCulture);
        return DateOnly.FromDateTime(dateTimeOffset.DateTime);
    }

    public override void Write(Utf8JsonWriter writer, DateOnly value, JsonSerializerOptions options)
    {
        var dateTimeOffset = new DateTimeOffset(value.ToDateTime(TimeOnly.MinValue), TimeSpan.Zero);
        writer.WriteStringValue(dateTimeOffset.ToString(DateTimeFormat, CultureInfo.InvariantCulture));
    }
}

#endif
