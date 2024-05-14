// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel;

/// <summary>
/// A custom JSON converter for converting function names in a JSON array.
/// This converter replaces dots used as a function name separator in prompts with hyphens when reading and back when writing.
/// </summary>
public sealed class FunctionNameFormatJsonConverter : JsonConverter<IList<string>>
{
    private const char PromptFunctionNameSeparator = '.';

    private const char FunctionNameSeparator = '-';

    /// <inheritdoc/>
    public override IList<string> Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        if (reader.TokenType != JsonTokenType.StartArray)
        {
            throw new JsonException("Expected a JSON array.");
        }

        var functionNames = new List<string>();

        while (reader.Read())
        {
            if (reader.TokenType == JsonTokenType.EndArray)
            {
                break;
            }

            if (reader.TokenType != JsonTokenType.String)
            {
                throw new JsonException("Expected a JSON string.");
            }

            var functionName = reader.GetString() ?? throw new JsonException("Expected a non-null JSON string.");

            functionNames.Add(functionName.Replace(PromptFunctionNameSeparator, FunctionNameSeparator));
        }

        return functionNames;
    }

    /// <inheritdoc/>
    public override void Write(Utf8JsonWriter writer, IList<string> value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();

        foreach (string functionName in value)
        {
            writer.WriteStringValue(functionName.Replace(FunctionNameSeparator, PromptFunctionNameSeparator));
        }

        writer.WriteEndArray();
    }
}
