// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Weaviate;

#pragma warning disable CA1812 // 'UnixSecondsDateTimeJsonConverter' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
[Obsolete("The IMemoryStore abstraction is being obsoleted, use Microsoft.Extensions.VectorData and WeaviateVectorStore")]
internal sealed class UnixSecondsDateTimeJsonConverter : JsonConverter<DateTime?>
#pragma warning restore CA1812 // 'UnixSecondsDateTimeJsonConverter' is an internal class that is apparently never instantiated. If so, remove the code from the assembly. If this class is intended to contain only static members, make it 'static' (Module in Visual Basic).
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
