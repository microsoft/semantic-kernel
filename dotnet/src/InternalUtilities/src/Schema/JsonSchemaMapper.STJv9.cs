// Copyright (c) Microsoft. All rights reserved.

#if NET9_0_OR_GREATER || SYSTEM_TEXT_JSON_V9
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics;
using System.Linq;
using System.Reflection;
using System.Text;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Text.Json.Schema;
using System.Text.Json.Serialization.Metadata;
using System.Threading.Tasks;

namespace JsonSchemaMapper;

#if EXPOSE_JSON_SCHEMA_MAPPER
public
#else
internal
#endif
    static partial class JsonSchemaMapper
{
    // For System.Text.Json v9 or greater, JsonSchemaMapper is implemented as a shim over the
    // built-in JsonSchemaExporter component. Added functionality is implemented by performing
    // fix-ups over the generated schema.

    private static partial JsonNode MapRootTypeJsonSchema(JsonTypeInfo typeInfo, JsonSchemaMapperConfiguration configuration)
    {
        JsonSchemaExporterOptions exporterOptions = new()
        {
            TreatNullObliviousAsNonNullable = configuration.TreatNullObliviousAsNonNullable,
            TransformSchemaNode = (JsonSchemaExporterContext ctx, JsonNode schema) => ApplySchemaTransformations(schema, ctx, configuration),
        };

        return JsonSchemaExporter.GetJsonSchemaAsNode(typeInfo, exporterOptions);
    }

    private static partial JsonNode MapMethodParameterJsonSchema(
        ParameterInfo parameterInfo,
        JsonTypeInfo parameterTypeInfo,
        JsonSchemaMapperConfiguration configuration,
        NullabilityInfoContext nullabilityContext,
        out bool isRequired)
    {
        Debug.Assert(parameterInfo.Name != null);

        JsonSchemaExporterOptions exporterOptions = new()
        {
            TreatNullObliviousAsNonNullable = configuration.TreatNullObliviousAsNonNullable,
            TransformSchemaNode = (JsonSchemaExporterContext ctx, JsonNode schema) => ApplySchemaTransformations(schema, ctx, configuration, parameterInfo.Name),
        };

        string? parameterDescription = null;
        isRequired = false;

        ResolveParameterInfo(
            parameterInfo,
            parameterTypeInfo,
            nullabilityContext,
            configuration,
            out bool hasDefaultValue,
            out JsonNode? defaultValue,
            out bool isNonNullableType,
            ref parameterDescription,
            ref isRequired);

        JsonNode parameterSchema = JsonSchemaExporter.GetJsonSchemaAsNode(parameterTypeInfo, exporterOptions);

        if (parameterDescription is not null)
        {
            ConvertSchemaToObject(ref parameterSchema).Insert(0, JsonSchemaConstants.DescriptionPropertyName, (JsonNode)parameterDescription);
        }

        if (hasDefaultValue)
        {
            ConvertSchemaToObject(ref parameterSchema).Add(JsonSchemaConstants.DefaultPropertyName, defaultValue);
        }

        if (isNonNullableType &&
            parameterSchema is JsonObject parameterSchemaObj &&
            parameterSchemaObj.TryGetPropertyValue(JsonSchemaConstants.TypePropertyName, out JsonNode? typeSchema) &&
            typeSchema is JsonArray typeArray)
        {
            for (int i = 0; i < typeArray.Count; i++)
            {
                if (typeArray[i]!.GetValue<string>() is "null")
                {
                    typeArray.RemoveAt(i);
                    break;
                }
            }

            if (typeArray.Count == 1)
            {
                parameterSchemaObj[JsonSchemaConstants.TypePropertyName] = (JsonNode)(string)typeArray[0]!;
            }
        }

        return parameterSchema;
    }

    private static JsonNode ApplySchemaTransformations(
        JsonNode schema,
        JsonSchemaExporterContext ctx,
        JsonSchemaMapperConfiguration configuration,
        string? parameterName = null)
    {
        JsonSchemaGenerationContext mapperCtx = new(
            ctx.TypeInfo,
            ctx.TypeInfo.Type,
            ctx.PropertyInfo,
            (ParameterInfo?)ctx.PropertyInfo?.AssociatedParameter?.AttributeProvider,
            ctx.PropertyInfo?.AttributeProvider);

        if (configuration.IncludeTypeInEnums)
        {
            if (ctx.TypeInfo.Type.IsEnum &&
                schema is JsonObject enumSchema &&
                enumSchema.ContainsKey(JsonSchemaConstants.EnumPropertyName))
            {
                enumSchema.Insert(0, JsonSchemaConstants.TypePropertyName, (JsonNode)"string");
            }
            else if (
                Nullable.GetUnderlyingType(ctx.TypeInfo.Type) is Type { IsEnum: true } &&
                schema is JsonObject nullableEnumSchema &&
                nullableEnumSchema.ContainsKey(JsonSchemaConstants.EnumPropertyName))
            {
                nullableEnumSchema.Insert(0, JsonSchemaConstants.TypePropertyName, new JsonArray() { (JsonNode)"string", (JsonNode)"null" });
            }
        }

        if (configuration.ResolveDescriptionAttributes && mapperCtx.GetAttribute<DescriptionAttribute>() is DescriptionAttribute attr)
        {
            ConvertSchemaToObject(ref schema).Insert(0, JsonSchemaConstants.DescriptionPropertyName, (JsonNode)attr.Description);
        }

        if (parameterName is null && configuration.IncludeSchemaVersion && ctx.Path.IsEmpty)
        {
            ConvertSchemaToObject(ref schema).Insert(0, JsonSchemaConstants.SchemaPropertyName, (JsonNode)SchemaVersion);
        }

        if (configuration.TransformSchemaNode is { } callback)
        {
            schema = callback(mapperCtx, schema);
        }

        if (parameterName != null && schema is JsonObject refObj &&
            refObj.TryGetPropertyValue(JsonSchemaConstants.RefPropertyName, out JsonNode? paramName))
        {
            // Fix up any $ref URIs to match the path from the root document.
            string refUri = paramName!.GetValue<string>();
            Debug.Assert(refUri is "#" || refUri.StartsWith("#/", StringComparison.Ordinal));
            refUri = refUri == "#"
                ? $"#/{JsonSchemaConstants.PropertiesPropertyName}/{parameterName}"
                : $"#/{JsonSchemaConstants.PropertiesPropertyName}/{parameterName}/{refUri[2..]}";

            refObj[JsonSchemaConstants.RefPropertyName] = (JsonNode)refUri;
        }

        return schema;
    }

    private static JsonObject ConvertSchemaToObject(ref JsonNode schema)
    {
        JsonObject jObj;

        switch (schema.GetValueKind())
        {
            case JsonValueKind.Object:
                return (JsonObject)schema;

            case JsonValueKind.False:
                schema = jObj = new() { [JsonSchemaConstants.NotPropertyName] = true };
                return jObj;

            default:
                Debug.Assert(schema.GetValueKind() is JsonValueKind.True, "invalid schema type.");
                schema = jObj = new JsonObject();
                return jObj;
        }
    }
}
#endif
