// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Orchestration;

/// <summary>
/// Converter for <see cref="ContextVariables"/> to/from JSON.
/// </summary>
public class ContextVariablesConverter : JsonConverter<ContextVariables>
{
    /// <summary>
    /// Read the JSON and convert to ContextVariables.
    /// </summary>
    /// <param name="reader">The JSON reader.</param>
    /// <param name="typeToConvert">The type to convert.</param>
    /// <param name="options">The JSON serializer options.</param>
    /// <returns>The deserialized <see cref="ContextVariables"/>.</returns>
    public override ContextVariables Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        var keyValuePairs = JsonSerializer.Deserialize<IEnumerable<KeyValuePair<string, string>>>(ref reader, options);
        var context = new ContextVariables();

        foreach (var kvp in keyValuePairs!)
        {
            if (string.IsNullOrWhiteSpace(kvp.Key))
            {
                // Json deserialization behaves differently in different versions of .NET. In some cases, the above "Deserialize" call
                // throws on a null key, and in others it does not. This check is to ensure that we throw in all cases.
                throw new JsonException("'Key' property cannot be null or empty.");
            }

            context.Set(kvp.Key, kvp.Value);
        }

        return context;
    }

    /// <summary>
    /// Write the ContextVariables to JSON.
    /// </summary>
    /// <param name="writer">The JSON writer.</param>
    /// <param name="value">The <see cref="ContextVariables"/> to write.</param>
    /// <param name="options">The JSON serializer options.</param>
    public override void Write(Utf8JsonWriter writer, ContextVariables value, JsonSerializerOptions options)
    {
        writer.WriteStartArray();

        foreach (var kvp in value)
        {
            writer.WriteStartObject();
            writer.WriteString("Key", kvp.Key);
            writer.WriteString("Value", kvp.Value);
            writer.WriteEndObject();
        }

        writer.WriteEndArray();
    }
}
