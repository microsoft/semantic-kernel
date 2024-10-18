// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using System.Reflection;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using JsonSchemaMapper;
using Microsoft.SemanticKernel;

namespace Step04;

internal static class JsonSchemaGenerator
{
    /// <summary>
    /// Wrapper for generating a JSON schema as string from a .NET type.
    /// </summary>
    public static string FromType<SchemaType>()
    {
        JsonSerializerOptions options = new(JsonSerializerOptions.Default)
        {
            UnmappedMemberHandling = JsonUnmappedMemberHandling.Disallow,
        };
        JsonSchemaMapperConfiguration config = new()
        {
            TreatNullObliviousAsNonNullable = true,
            TransformSchemaNode = (context, schema) =>
            {
                // NOTE: This can be replaced with `IncludeAdditionalProperties = false` when upgraded to System.Json.Text 9.0.0
                if (context.TypeInfo.Type == typeof(SchemaType))
                {
                    schema["additionalProperties"] = false;
                }

                // Determine if a type or property and extract the relevant attribute provider
                ICustomAttributeProvider? attributeProvider = context.PropertyInfo is not null
                    ? context.PropertyInfo.AttributeProvider
                    : context.TypeInfo.Type;

                // Look up any description attributes
                DescriptionAttribute? descriptionAttr = attributeProvider?
                    .GetCustomAttributes(inherit: true)
                    .Select(attr => attr as DescriptionAttribute)
                    .FirstOrDefault(attr => attr is not null);

                // Apply description attribute to the generated schema
                if (descriptionAttr != null)
                {
                    if (schema is not JsonObject jObj)
                    {
                        // Handle the case where the schema is a boolean
                        JsonValueKind valueKind = schema.GetValueKind();
                        schema = jObj = new JsonObject();
                        if (valueKind is JsonValueKind.False)
                        {
                            jObj.Add("not", true);
                        }
                    }

                    jObj["description"] = descriptionAttr.Description;
                }

                return schema;
            }
        };

        return KernelJsonSchemaBuilder.Build(null, typeof(SchemaType), "Intent Result", config).AsJson();
    }
}
