// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.Memory.Chroma;

/// <summary>
/// JSON Converter for Chroma boolean values.
/// </summary>
public class ChromaBooleanConverter : JsonConverter<bool>
{
    /// <inheritdoc/>
    public override bool Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (!reader.TryGetInt16(out short value))
        {
            return false;
        }

        return Convert.ToBoolean(value);
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, bool value, JsonSerializerOptions options)
    {
        writer.WriteNumberValue(Convert.ToDecimal(value));
    }
}
