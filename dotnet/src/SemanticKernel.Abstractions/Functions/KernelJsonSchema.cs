// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Json.Schema;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel;

/// <summary>Represents JSON Schema for describing types used in <see cref="KernelFunction"/>s.</summary>
[JsonConverter(typeof(KernelJsonSchema.JsonConverter))]
public sealed class KernelJsonSchema
{
    /// <summary>Converter for serializing/deserializing JsonSchema instances.</summary>
    private static readonly SchemaJsonConverter s_jsonSchemaConverter = new();
    /// <summary>Serialization settings for <see cref="JsonSerializer"/></summary>
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { MaxDepth = 128 };
    /// <summary>The schema stored as a string.</summary>
    private string? _schemaAsString;

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="jsonSchema">The JSON Schema as a string.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>, or null if <paramref name="jsonSchema"/> is null or empty.</returns>
    internal static KernelJsonSchema? ParseOrNull(string? jsonSchema) =>
        !string.IsNullOrEmpty(jsonSchema) ? new(JsonSerializer.Deserialize<JsonElement>(jsonSchema!, s_jsonSerializerOptions)) :
        null;

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="jsonSchema">The JSON Schema as a string.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="jsonSchema"/> is null.</exception>
    /// <exception cref="JsonException">The JSON is invalid.</exception>
    public static KernelJsonSchema Parse(string jsonSchema) =>
        new(JsonSerializer.SerializeToElement(JsonSchema.FromText(jsonSchema, s_jsonSerializerOptions), s_jsonSerializerOptions));

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="jsonSchema">The JSON Schema as a sequence of UTF16 chars.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>.</returns>
    /// <exception cref="JsonException">The JSON is invalid.</exception>
    public static KernelJsonSchema Parse(ReadOnlySpan<char> jsonSchema) =>
        new(JsonSerializer.SerializeToElement(JsonSerializer.Deserialize<JsonSchema>(jsonSchema, s_jsonSerializerOptions), s_jsonSerializerOptions));

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="utf8JsonSchema">The JSON Schema as a sequence of UTF8 bytes.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>.</returns>
    /// <exception cref="JsonException">The JSON is invalid.</exception>
    public static KernelJsonSchema Parse(ReadOnlySpan<byte> utf8JsonSchema) =>
        new(JsonSerializer.SerializeToElement(JsonSerializer.Deserialize<JsonSchema>(utf8JsonSchema, s_jsonSerializerOptions), s_jsonSerializerOptions));

    /// <summary>Initializes a new instance from the specified <see cref="JsonElement"/>.</summary>
    /// <param name="jsonSchema">The schema to be stored.</param>
    /// <remarks>
    /// The <paramref name="jsonSchema"/> is not validated, which is why this constructor is internal.
    /// All callers must ensure JSON Schema validity.
    /// </remarks>
    internal KernelJsonSchema(JsonElement jsonSchema) =>
        this.RootElement = jsonSchema;

    /// <summary>Gets a <see cref="JsonElement"/> representing the root element of the schema.</summary>
    public JsonElement RootElement { get; }

    /// <summary>Gets the JSON Schema as a string.</summary>
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonOptionsCache.WriteIndented);

    /// <summary>Converter for reading/writing the schema.</summary>
    public sealed class JsonConverter : JsonConverter<KernelJsonSchema>
    {
        /// <inheritdoc/>
        public override KernelJsonSchema? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
            new(JsonSerializer.SerializeToElement(s_jsonSchemaConverter.Read(ref reader, typeToConvert, options)));

        /// <inheritdoc/>
        public override void Write(Utf8JsonWriter writer, KernelJsonSchema value, JsonSerializerOptions options) =>
            value.RootElement.WriteTo(writer);
    }
}
