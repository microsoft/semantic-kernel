// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Agents.Serialization;

/// <summary>
/// Translates the serialized state to avoid escaping nested JSON as string.
/// </summary>
/// <example>
/// Without converter:
/// <code>
/// {
///   "state": "{\"key\":\"value\"}"
/// }
/// </code>
///
/// With converter:
/// <code>
/// {
///   "state": {"key": "value"}
/// }
/// </code>
///
/// Always:
/// <code>
/// {
///   "state": "text",
/// }
/// </code>
/// </example>
internal class JsonChannelStateConverter : JsonConverter<string>
{
    /// <inheritdoc/>
    public override string? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType == JsonTokenType.String)
        {
            string? token = reader.GetString();
            return token;
        }

        using var doc = JsonDocument.ParseValue(ref reader);
        return doc.RootElement.GetRawText();
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, string value, JsonSerializerOptions options)
    {
        if ((value.StartsWith("[", StringComparison.Ordinal) && value.EndsWith("]", StringComparison.Ordinal)) ||
            (value.StartsWith("{", StringComparison.Ordinal) && value.EndsWith("}", StringComparison.Ordinal)))
        {
            writer.WriteRawValue(value);
        }
        else
        {
            writer.WriteStringValue(value);
        }
    }
}
