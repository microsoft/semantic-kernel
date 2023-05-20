// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Weaviate.Http.JsonConverter;

internal sealed class UnixSecondsDateTimeJsonConverter : JsonConverter<DateTime?>
{
    private static readonly DateTime s_unixDateTime = new(1970, 1, 1, 0, 0, 0, 0, DateTimeKind.Utc);

    public override DateTime? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (!reader.TryGetInt64(out long value))
        {
            return null;
        }

        return s_unixDateTime.AddTicks(value).ToLocalTime();
    }

    public override void Write(Utf8JsonWriter writer, DateTime? value, JsonSerializerOptions options)
    {
        if (value.HasValue)
        {
            writer.WriteNumberValue(new DateTimeOffset(value.Value.ToUniversalTime()).Ticks);
        }
        else
        {
            writer.WriteNullValue();
        }
    }
}
