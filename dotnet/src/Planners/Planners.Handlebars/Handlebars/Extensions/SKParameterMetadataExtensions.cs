// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;

#pragma warning disable IDE0130 // Namespace does not match folder structure
namespace Microsoft.SemanticKernel.Planning.Handlebars;
#pragma warning restore IDE0130

internal static class SKParameterMetadataExtensions
{
    /// <summary>
    /// Checks if type is primitive or string
    /// </summary>
    public static bool IsPrimitiveOrStringType(Type type) => type.IsPrimitive || type == typeof(string);

    /// <summary>
    /// Checks if stringified type is primitive or string
    /// </summary>
    public static bool IsPrimitiveOrStringType(string type) =>
        type == "string" || type == "number" || type == "integer" || type == "boolean";

    /// <summary>
    /// Converts non-primitive types to a data class definition and returns a hash set of complex type metadata.
    /// Complex types will become a data class.
    /// If there are nested complex types, the nested complex type will also be returned.
    /// Example:
    /// Complex type:
    /// class ComplexType:
    ///    propertyA: int
    ///    propertyB: str
    ///    propertyC: PropertyC
    /// </summary>
    public static HashSet<HandlebarsParameterTypeMetadata> ToHandlebarsParameterTypeMetadata(this Type type)
    {
        var parameterTypes = new HashSet<HandlebarsParameterTypeMetadata>();
        if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(Task<>))
        {
            // Async return type - need to extract the actual return type
            var actualReturnType = type.GenericTypeArguments[0]; // Actual Return Type
            var returnTypeProperties = actualReturnType.GetProperties();

            if (!IsPrimitiveOrStringType(actualReturnType) && returnTypeProperties.Length is not 0)
            {
                parameterTypes.Add(new HandlebarsParameterTypeMetadata()
                {
                    Name = actualReturnType.Name,
                    IsComplex = true,
                    Properties = returnTypeProperties.Select(p => new SKParameterMetadata(p.Name) { ParameterType = p.PropertyType }).ToList()
                });

                parameterTypes.AddNestedComplexTypes(returnTypeProperties);
            }
        }
        else if (type.IsClass && type != typeof(string))
        {
            // Class
            var properties = type.GetProperties();

            parameterTypes.Add(new HandlebarsParameterTypeMetadata()
            {
                Name = type.Name,
                IsComplex = properties.Length is not 0,
                Properties = properties.Select(p => new SKParameterMetadata(p.Name) { ParameterType = p.PropertyType }).ToList()
            });

            parameterTypes.AddNestedComplexTypes(properties);
        }

        return parameterTypes;
    }

    private static void AddNestedComplexTypes(this HashSet<HandlebarsParameterTypeMetadata> parameterTypes, PropertyInfo[] properties)
    {
        // Add nested complex types
        foreach (var property in properties)
        {
            parameterTypes.UnionWith(property.PropertyType.ToHandlebarsParameterTypeMetadata());
        }
    }

    private static Type GetTypeFromSchema(string schemaType)
    {
        var typeMap = new Dictionary<string, Type>
            {
                {"string", typeof(string)},
                {"integer", typeof(long)},
                {"number", typeof(double)},
                {"boolean", typeof(bool)},
                {"object", typeof(object)},
                {"array", typeof(object[])},
                // If type is null, default to object
                {"null", typeof(object)}
            };

        return typeMap[schemaType];
    }

    public static SKParameterMetadata ParseJsonSchema(this SKParameterMetadata parameter)
    {
        var schema = parameter.Schema!;
        var type = schema.RootElement.GetProperty("type").GetString() ?? "object";
        if (IsPrimitiveOrStringType(type) || type == "null")
        {
            return new(parameter)
            {
                ParameterType = GetTypeFromSchema(type),
                Schema = null
            };
        }

        return parameter;
    }

    public static string ToJsonString(this JsonElement jsonProperties)
    {
        var options = new JsonSerializerOptions()
        {
            WriteIndented = true,
        };

        return JsonSerializer.Serialize(jsonProperties, options);
    }

    public static string GetSchemaTypeName(this SKParameterMetadata parameter)
    {
        var schemaType = parameter.Schema is not null && parameter.Schema.RootElement.TryGetProperty("type", out var typeElement) ? typeElement.ToString() : "object";
        return $"{parameter.Name}-{schemaType}";
    }

    public static SKParameterMetadata ToSKParameterMetadata(this SKReturnParameterMetadata parameter, string functionName) => new($"{functionName}Returns")
    {
        Description = parameter.Description,
        ParameterType = parameter.ParameterType,
        Schema = parameter.Schema
    };

    public static SKReturnParameterMetadata ToSKReturnParameterMetadata(this SKParameterMetadata parameter) => new()
    {
        Description = parameter.Description,
        ParameterType = parameter.ParameterType,
        Schema = parameter.Schema
    };
}
