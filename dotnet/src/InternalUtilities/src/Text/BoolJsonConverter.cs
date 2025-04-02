// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Deserializes a bool from a string. This is useful when deserializing a <see cref="PromptExecutionSettings"/> instance that contains bool properties.
/// Serializing a <see cref="PromptExecutionSettings"/> instance without this converter will throw a 'System.Text.Json.JsonException : The JSON value could not be converted to System.Nullable'
/// if there are any bool properties.
/// </summary>
internal sealed class BoolJsonConverter : JsonConverter<bool?>
{
    /// <inheritdoc/>
    public override bool? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType == JsonTokenType.String)
        {
            string? value = reader.GetString();
            if (value is null)
            {
                return null;
            }
            if (value.Equals("true", StringComparison.OrdinalIgnoreCase))
            {
                return true;
            }
            else if (value.Equals("false", StringComparison.OrdinalIgnoreCase))
            {
                return false;
            }

            throw new ArgumentException($"Value '{value}' can be parsed as a boolean value");
        }
        else if (reader.TokenType == JsonTokenType.True)
        {
            return true;
        }
        else if (reader.TokenType == JsonTokenType.False)
        {
            return false;
        }

        throw new ArgumentException($"Invalid token type found '{reader.TokenType}', expected a boolean value.");
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, bool? value, JsonSerializerOptions options)
    {
        if (value is null)
        {
            writer.WriteNullValue();
        }
        else
        {
            writer.WriteBooleanValue((bool)value);
        }
    }
}
