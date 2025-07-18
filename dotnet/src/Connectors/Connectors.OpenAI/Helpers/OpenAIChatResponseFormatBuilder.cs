// Copyright (c) Microsoft. All rights reserved.

using System;
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
            bool? isStrict = jsonSchemaProperty.TryGetProperty("strict", out var isStrictProperty) && isStrictProperty.ValueKind == JsonValueKind.True ? true : null;

            BinaryData schemaBinaryData = new(Encoding.UTF8.GetBytes(schema));

            return ChatResponseFormat.CreateJsonSchemaFormat(schemaName, schemaBinaryData, jsonSchemaIsStrict: isStrict);
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

    #region private

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
