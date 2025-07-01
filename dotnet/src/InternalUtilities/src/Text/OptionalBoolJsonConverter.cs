// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Text;

#pragma warning disable CA1812 // Instantiated via JsonConverterAttribute

/// <summary>
/// Deserializes a bool from a string. This is useful when deserializing a <see cref="PromptExecutionSettings"/> instance that contains bool properties.
/// Serializing a <see cref="PromptExecutionSettings"/> instance without this converter will throw a 'System.Text.Json.JsonException : The JSON value could not be converted to System.Nullable'
/// if there are any bool properties.
/// </summary>
[ExcludeFromCodeCoverage]
internal sealed class OptionalBoolJsonConverter : JsonConverter<bool?>
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
            if (bool.TryParse(value, out var boolValue))
            {
                return boolValue;
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
        else if (reader.TokenType == JsonTokenType.Null)
        {
            return null;
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
