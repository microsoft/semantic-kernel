// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
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
        if (schema is JsonObject jsonSchemaObject)
        {
            var types = GetTypes(jsonSchemaObject);

            if (types is not null && types.Contains(ObjectValueName))
            {
                // Set "additionalProperties" to "false".
                jsonSchemaObject[AdditionalPropertiesPropertyName] = false;

                // Specify all properties as "required".
                if (jsonSchemaObject.TryGetPropertyValue(PropertiesPropertyName, out var properties) &&
                    properties is JsonObject propertiesObject)
                {
                    var propertyNames = propertiesObject.Select(l => (JsonNode)l.Key).ToArray();

                    jsonSchemaObject[RequiredPropertyName] = new JsonArray(propertyNames);
                }
            }
        }

        return schema;
    }

    private static List<string?>? GetTypes(JsonObject jsonObject)
    {
        if (jsonObject.TryGetPropertyValue(TypePropertyName, out var typeProperty) && typeProperty is not null)
        {
            // For cases when "type" has an array value (e.g "type": "["object", "null"]").
            if (typeProperty is JsonArray nodeArray)
            {
                return nodeArray.ToArray().Select(element => element?.GetValue<string>()).ToList();
            }

            // Case when "type" has a string value (e.g. "type": "object").
            return [typeProperty.GetValue<string>()];
        }

        return null;
    }
}
