// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel;

/// <summary>Represents JSON Schema for describing types used in <see cref="KernelFunction"/>s.</summary>
[JsonConverter(typeof(KernelJsonSchema.JsonConverter))]
public sealed class KernelJsonSchema
{
    /// <summary>Serialization settings for <see cref="JsonSerializer"/></summary>
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { MaxDepth = 128 };
    /// <summary>The schema stored as a string.</summary>
    private string? _schemaAsString;

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="jsonSchema">The JSON Schema as a string.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>, or null if <paramref name="jsonSchema"/> is null or empty.</returns>
    internal static KernelJsonSchema? ParseOrNull(string? jsonSchema) =>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        !string.IsNullOrEmpty(jsonSchema) ? new(JsonSerializer.Deserialize<JsonElement>(jsonSchema!, s_jsonSerializerOptions)) :
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        !string.IsNullOrEmpty(jsonSchema) ? new(JsonSerializer.Deserialize<JsonElement>(jsonSchema!, s_jsonSerializerOptions)) :
=======
        !string.IsNullOrEmpty(jsonSchema) ? new(JsonSerializer.Deserialize<JsonElement>(jsonSchema!, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement)) :
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        !string.IsNullOrEmpty(jsonSchema) ? new(JsonSerializer.Deserialize<JsonElement>(jsonSchema!, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement)) :
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        null;

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="jsonSchema">The JSON Schema as a string.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>.</returns>
    /// <exception cref="ArgumentException"><paramref name="jsonSchema"/> is null.</exception>
    /// <exception cref="JsonException">The JSON is invalid.</exception>
    public static KernelJsonSchema Parse(string jsonSchema) =>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, s_jsonSerializerOptions));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, s_jsonSerializerOptions));
=======
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement));
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement));
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="jsonSchema">The JSON Schema as a sequence of UTF16 chars.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>.</returns>
    /// <exception cref="JsonException">The JSON is invalid.</exception>
    public static KernelJsonSchema Parse(ReadOnlySpan<char> jsonSchema) =>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, s_jsonSerializerOptions));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, s_jsonSerializerOptions));
=======
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement));
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        new(JsonSerializer.Deserialize<JsonElement>(jsonSchema, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement));
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

    /// <summary>Parses a JSON Schema for a parameter type.</summary>
    /// <param name="utf8JsonSchema">The JSON Schema as a sequence of UTF8 bytes.</param>
    /// <returns>A parsed <see cref="KernelJsonSchema"/>.</returns>
    /// <exception cref="JsonException">The JSON is invalid.</exception>
    public static KernelJsonSchema Parse(ReadOnlySpan<byte> utf8JsonSchema) =>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        new(JsonSerializer.Deserialize<JsonElement>(utf8JsonSchema, s_jsonSerializerOptions));
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
        new(JsonSerializer.Deserialize<JsonElement>(utf8JsonSchema, s_jsonSerializerOptions));
=======
        new(JsonSerializer.Deserialize<JsonElement>(utf8JsonSchema, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement));
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        new(JsonSerializer.Deserialize<JsonElement>(utf8JsonSchema, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement));
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonOptionsCache.WriteIndented);
=======
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement);
>>>>>>> Stashed changes
=======
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement);
>>>>>>> Stashed changes
=======
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement);
>>>>>>> Stashed changes
=======
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement);
>>>>>>> Stashed changes
=======
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement);
>>>>>>> Stashed changes
=======
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement);
>>>>>>> origin/main
=======
    public override string ToString() => this._schemaAsString ??= JsonSerializer.Serialize(this.RootElement, JsonElementJsonSerializerContext.MaxDepth_128.JsonElement);
>>>>>>> Stashed changes

    /// <summary>Converter for reading/writing the schema.</summary>
    public sealed class JsonConverter : JsonConverter<KernelJsonSchema>
    {
        /// <inheritdoc/>
        public override KernelJsonSchema? Read(ref Utf8JsonReader reader, Type typeToConvert, JsonSerializerOptions options) =>
            new(JsonElement.ParseValue(ref reader));

        /// <inheritdoc/>
        public override void Write(Utf8JsonWriter writer, KernelJsonSchema value, JsonSerializerOptions options) =>
            value.RootElement.WriteTo(writer);
    }
}
