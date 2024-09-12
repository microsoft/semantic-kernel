// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Linq;
using System.Text.Json.Nodes;
using JsonSchemaMapper;

namespace Microsoft.SemanticKernel.Connectors.OpenAI;

/// <summary>
/// JSON Schema transformer to apply OpenAI conditions for structured outputs.
/// <para>
/// - "additionalProperties" property must always be set to <see langword="false"/> in objects.
/// More information here: <see href="https://platform.openai.com/docs/guides/structured-outputs/additionalproperties-false-must-always-be-set-in-objects"/>.
/// </para>
/// <para>
/// - All fields must be "required".
/// More information here: <see href="https://platform.openai.com/docs/guides/structured-outputs/all-fields-must-be-required"/>.
/// </para>
/// </summary>
internal static class OpenAIJsonSchemaTransformer
{
    private const string AdditionalPropertiesPropertyName = "additionalProperties";
    private const string TypePropertyName = "type";
    private const string ObjectValueName = "object";
    private const string PropertiesPropertyName = "properties";
    private const string RequiredPropertyName = "required";

    internal static JsonNode Transform(JsonSchemaGenerationContext context, JsonNode schema)
    {
        // Transform schema if node is object only.
        if (schema is JsonObject jsonSchemaObject &&
            jsonSchemaObject.TryGetPropertyValue(TypePropertyName, out var typeProperty) &&
            typeProperty is not null)
        {
            var type = typeProperty.GetValue<string>();

            if (type.Equals(ObjectValueName, StringComparison.OrdinalIgnoreCase))
            {
                // Set "additionalProperties" to "false".
                jsonSchemaObject[AdditionalPropertiesPropertyName] = JsonValue.Create(false);

                // Specify all properties as "required".
                if (jsonSchemaObject.TryGetPropertyValue(PropertiesPropertyName, out var properties) &&
                    properties is JsonObject propertiesObject)
                {
                    var propertyNames = propertiesObject.Select(l => JsonValue.Create(l.Key)).ToArray();

                    jsonSchemaObject[RequiredPropertyName] = new JsonArray(propertyNames);
                }
            }
        }

        return schema;
    }
}
