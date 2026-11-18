// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ClientModel.Primitives;
using System.Text;
using System.Text.Json;
using OpenAI.Chat;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// Helper class to build <see cref="ChatResponseFormat"/> object.
/// </summary>
internal static class OpenAIChatResponseFormatBuilder
{
    /// <summary>
    /// <see cref="Microsoft.Extensions.AI.AIJsonSchemaCreateOptions"/> for JSON schema format for structured outputs.
    /// </summary>
    private static readonly Microsoft.Extensions.AI.AIJsonSchemaCreateOptions s_jsonSchemaCreateOptions = new()
    {
        TransformOptions = new()
        {
            DisallowAdditionalProperties = true,
            RequireAllProperties = true,
            MoveDefaultKeywordToDescription = true,
        }
    };

    /// <summary>
    /// Gets instance of <see cref="ChatResponseFormat"/> object for JSON schema format for structured outputs from <see cref="JsonElement"/>.
    /// </summary>
    internal static ChatResponseFormat GetJsonSchemaResponseFormat(JsonElement responseFormatElement)
    {
        const string DefaultSchemaName = "JsonSchema";

        if (responseFormatElement.TryGetProperty("type", out var typeProperty) &&
            typeProperty.GetString()?.Equals("json_schema", StringComparison.Ordinal) is true &&
            responseFormatElement.TryGetProperty("json_schema", out var jsonSchemaProperty))
        {
            string schema = jsonSchemaProperty.TryGetProperty("schema", out var schemaProperty) ? schemaProperty.ToString() : throw new ArgumentException("Property 'schema' is not initialized in JSON schema response format.");
            string? schemaName = jsonSchemaProperty.TryGetProperty("name", out var nameProperty) ? nameProperty.GetString() : DefaultSchemaName;
            string? schemaDescription = jsonSchemaProperty.TryGetProperty("description", out var descriptionProperty) && descriptionProperty.ValueKind == JsonValueKind.String ? descriptionProperty.GetString() : null;
            bool? isStrict = jsonSchemaProperty.TryGetProperty("strict", out var isStrictProperty) && isStrictProperty.ValueKind == JsonValueKind.True ? true : null;

            BinaryData schemaBinaryData = new(Encoding.UTF8.GetBytes(schema));

            return ChatResponseFormat.CreateJsonSchemaFormat(schemaName, schemaBinaryData, schemaDescription, isStrict);
        }

        return ChatResponseFormat.CreateJsonSchemaFormat(
            DefaultSchemaName,
            new BinaryData(Encoding.UTF8.GetBytes(responseFormatElement.ToString())));
    }

    /// <summary>
    /// Gets instance of <see cref="ChatResponseFormat"/> object for JSON schema format for structured outputs from type.
    /// </summary>
    internal static ChatResponseFormat GetJsonSchemaResponseFormat(Type formatObjectType)
    {
        var type = formatObjectType.IsGenericType && formatObjectType.GetGenericTypeDefinition() == typeof(Nullable<>) ? Nullable.GetUnderlyingType(formatObjectType)! : formatObjectType;

        var schema = KernelJsonSchemaBuilder.Build(type, configuration: s_jsonSchemaCreateOptions);
        var schemaBinaryData = BinaryData.FromString(schema.ToString());

        var typeName = GetTypeName(type);

        return ChatResponseFormat.CreateJsonSchemaFormat(typeName, schemaBinaryData, jsonSchemaIsStrict: true);
    }

    /// <summary>
    /// Gets the <see cref="ChatResponseFormat"/> for a response format value when it is a strict JSON schema; otherwise, <see langword="null"/>.
    /// </summary>
    internal static ChatResponseFormat? GetStrictJsonSchemaResponseFormat(object? responseFormat)
    {
        switch (responseFormat)
        {
            case Type formatObjectType:
                // Type-based formats are always created as strict JSON schemas.
                return GetJsonSchemaResponseFormat(formatObjectType);

            case ChatResponseFormat formatObject:
                // ChatResponseFormat does not expose its strictness, so inspect its OpenAI wire representation.
                using (JsonDocument document = JsonDocument.Parse(ModelReaderWriter.Write(formatObject).ToMemory()))
                {
                    return IsStrictJsonSchema(document.RootElement) ? formatObject : null;
                }

            case JsonElement formatElement when IsStrictJsonSchema(formatElement):
                // Only well-formed strict envelopes are converted, so malformed values keep their existing behavior.
                return GetJsonSchemaResponseFormat(formatElement);

            default:
                return null;
        }
    }

    #region private

    /// <summary>
    /// Determines whether a JSON value is a <c>json_schema</c> response format envelope with a schema and <c>strict</c> set to <see langword="true"/>.
    /// </summary>
    private static bool IsStrictJsonSchema(JsonElement responseFormat) =>
        responseFormat.ValueKind == JsonValueKind.Object &&
        responseFormat.TryGetProperty("type", out JsonElement type) &&
        type.ValueKind == JsonValueKind.String &&
        type.ValueEquals("json_schema") &&
        responseFormat.TryGetProperty("json_schema", out JsonElement jsonSchema) &&
        jsonSchema.ValueKind == JsonValueKind.Object &&
        jsonSchema.TryGetProperty("schema", out _) &&
        jsonSchema.TryGetProperty("strict", out JsonElement strict) &&
        strict.ValueKind == JsonValueKind.True;

    /// <summary>
    /// Returns a type name concatenated with generic argument type names if they exist.
    /// </summary>
    private static string GetTypeName(Type type)
    {
        if (!type.IsGenericType)
        {
            return type.Name;
        }

        // If type is generic, base name is followed by ` character.
        string baseName = type.Name.Substring(0, type.Name.IndexOf('`'));

        Type[] typeArguments = type.GetGenericArguments();
        string argumentNames = string.Concat(Array.ConvertAll(typeArguments, GetTypeName));

        return $"{baseName}{argumentNames}";
    }

    #endregion
}
