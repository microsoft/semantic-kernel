// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

internal sealed class TypeOrFunctionResponseFormatConverter : JsonConverter<object>
{
    /// <summary>
    /// Determines whether the specified type can be converted by this converter.
    /// </summary>
    /// <param name="typeToConvert">The type to evaluate for conversion capability.</param>
    /// <returns><see langword="true"/> if the specified type is <see cref="object"/>; otherwise, <see langword="false"/>.</returns>
    public override bool CanConvert(Type typeToConvert)
    {
        return typeToConvert == typeof(object);
    }

    /// <summary>
    /// reads the JSON representation of the object.
    /// </summary>
    /// <param name="reader">The reader to use for deserialization.</param>
    /// <param name="typeToConvert">The type to convert.</param>
    /// <param name="options">The options to use for deserialization.</param>
    /// <returns></returns>
    public override object? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options)
    {
        return JsonSerializer.Deserialize<JsonElement>(ref reader, options);
    }

    /// <summary>
    /// writes the JSON representation of the object.
    /// </summary>
    /// <param name="writer">The writer to use for serialization.</param>
    /// <param name="value">The value to serialize.</param>
    /// <param name="options">The options to use for serialization.</param>
    public override void Write(Utf8JsonWriter writer, object value, JsonSerializerOptions options)
    {
        if (value is Type type)
        {
            var responseFormat = OpenAIChatResponseFormatBuilder.GetJsonSchemaResponseFormat(type);
            JsonSerializer.Serialize(writer, responseFormat, options);
        }
        else
        {
            JsonSerializer.Serialize(writer, value, value.GetType(), options);
        }
    }
}
