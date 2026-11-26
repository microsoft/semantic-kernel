// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
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
        var schemaNode = JsonNode.Parse(schema.ToString()) ?? throw new InvalidOperationException("Generated JSON schema cannot be parsed.");
        MoveNestedReferencesToDefinitions(schemaNode);
        var schemaBinaryData = BinaryData.FromString(schemaNode.ToJsonString());

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

    /// <summary>
    /// Moves local references that point to nested schemas into top-level $defs entries.
    /// </summary>
    private static void MoveNestedReferencesToDefinitions(JsonNode schema)
    {
        if (schema is not JsonObject root)
        {
            return;
        }

        Dictionary<string, string> movedReferences = new(StringComparer.Ordinal);
        HashSet<string> usedDefinitionNames = new(StringComparer.Ordinal);

        if (root.TryGetPropertyValue("$defs", out JsonNode? existingDefinitions) && existingDefinitions is JsonObject definitions)
        {
            foreach (var definition in definitions)
            {
                usedDefinitionNames.Add(definition.Key);
            }
        }

        while (MoveNestedReferencesToDefinitionsCore(schema, root, movedReferences, usedDefinitionNames))
        {
        }
    }

    private static bool MoveNestedReferencesToDefinitionsCore(
        JsonNode? schema,
        JsonObject root,
        Dictionary<string, string> movedReferences,
        HashSet<string> usedDefinitionNames)
    {
        bool moved = false;

        switch (schema)
        {
            case JsonObject schemaObject:
                if (schemaObject.TryGetPropertyValue("$ref", out JsonNode? referenceNode) &&
                    referenceNode?.GetValueKind() == JsonValueKind.String)
                {
                    string reference = referenceNode.GetValue<string>();
                    if (ShouldMoveReference(reference))
                    {
                        if (!movedReferences.TryGetValue(reference, out string? definitionName))
                        {
                            JsonNode? target = ResolveJsonPointer(root, reference);
                            if (target is not null)
                            {
                                definitionName = CreateDefinitionName(reference, usedDefinitionNames);
                                GetOrCreateDefinitions(root)[definitionName] = target.DeepClone();
                                movedReferences[reference] = definitionName;
                                moved = true;
                            }
                        }

                        if (definitionName is not null)
                        {
                            string topLevelReference = $"#/$defs/{EscapeJsonPointerSegment(definitionName)}";
                            if (!StringComparer.Ordinal.Equals(reference, topLevelReference))
                            {
                                schemaObject["$ref"] = topLevelReference;
                                moved = true;
                            }
                        }
                    }
                }

                foreach (var property in new List<KeyValuePair<string, JsonNode?>>(schemaObject))
                {
                    moved |= MoveNestedReferencesToDefinitionsCore(property.Value, root, movedReferences, usedDefinitionNames);
                }

                break;

            case JsonArray schemaArray:
                foreach (JsonNode? item in schemaArray)
                {
                    moved |= MoveNestedReferencesToDefinitionsCore(item, root, movedReferences, usedDefinitionNames);
                }

                break;
        }

        return moved;
    }

    private static bool ShouldMoveReference(string reference)
        => reference.StartsWith("#/", StringComparison.Ordinal) &&
            !reference.StartsWith("#/$defs/", StringComparison.Ordinal) &&
            !reference.StartsWith("#/definitions/", StringComparison.Ordinal);

    private static JsonObject GetOrCreateDefinitions(JsonObject root)
    {
        if (root.TryGetPropertyValue("$defs", out JsonNode? definitionsNode) && definitionsNode is JsonObject definitions)
        {
            return definitions;
        }

        definitions = [];
        root["$defs"] = definitions;

        return definitions;
    }

    private static JsonNode? ResolveJsonPointer(JsonNode root, string reference)
    {
        JsonNode? current = root;
        string[] segments = reference.Substring(2).Split('/');

        foreach (string segment in segments)
        {
            string unescapedSegment = UnescapeJsonPointerSegment(segment);

            switch (current)
            {
                case JsonObject currentObject when currentObject.TryGetPropertyValue(unescapedSegment, out JsonNode? propertyValue):
                    current = propertyValue;
                    break;

                case JsonArray currentArray when int.TryParse(unescapedSegment, out int index) && index >= 0 && index < currentArray.Count:
                    current = currentArray[index];
                    break;

                default:
                    return null;
            }
        }

        return current;
    }

    private static string CreateDefinitionName(string reference, HashSet<string> usedDefinitionNames)
    {
        string[] segments = reference.Substring(2).Split('/');
        StringBuilder nameBuilder = new();

        foreach (string segment in segments)
        {
            string unescapedSegment = UnescapeJsonPointerSegment(segment);

            if (StringComparer.Ordinal.Equals(unescapedSegment, "properties"))
            {
                continue;
            }

            bool capitalizeNext = true;
            foreach (char character in unescapedSegment)
            {
                if (!char.IsLetterOrDigit(character))
                {
                    capitalizeNext = true;
                    continue;
                }

                nameBuilder.Append(capitalizeNext ? char.ToUpperInvariant(character) : character);
                capitalizeNext = false;
            }
        }

        string baseName = nameBuilder.Length > 0 ? nameBuilder.ToString() : "SchemaDefinition";
        string name = baseName;
        int suffix = 2;

        while (!usedDefinitionNames.Add(name))
        {
            name = $"{baseName}{suffix++}";
        }

        return name;
    }

    private static string EscapeJsonPointerSegment(string segment)
        => segment.Replace("~", "~0").Replace("/", "~1");

    private static string UnescapeJsonPointerSegment(string segment)
        => segment.Replace("~1", "/").Replace("~0", "~");

    #endregion
}
