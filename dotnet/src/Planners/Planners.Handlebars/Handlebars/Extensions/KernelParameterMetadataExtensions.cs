// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

internal static class KernelParameterMetadataExtensions
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
        return type.ToHandlebarsParameterTypeMetadata(new HashSet<Type>());
    }

    private static HashSet<HandlebarsParameterTypeMetadata> ToHandlebarsParameterTypeMetadata(this Type type, HashSet<Type> processedTypes)
    {
        var parameterTypes = new HashSet<HandlebarsParameterTypeMetadata>();
        if (type.TryGetGenericResultType(out var taskResultType))
        {
            var resultTypeProperties = taskResultType.GetProperties();
            if (!IsPrimitiveOrStringType(taskResultType) && resultTypeProperties.Length is not 0)
            {
                parameterTypes.Add(new HandlebarsParameterTypeMetadata()
                {
                    Name = taskResultType.Name,
                    IsComplex = true,
                    Properties = resultTypeProperties.Select(p => new KernelParameterMetadata(p.Name) { ParameterType = p.PropertyType }).ToList()
                });

                processedTypes.Add(taskResultType);
                parameterTypes.AddNestedComplexTypes(resultTypeProperties, processedTypes);
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
                Properties = properties.Select(p => new KernelParameterMetadata(p.Name) { ParameterType = p.PropertyType }).ToList()
            });

            processedTypes.Add(type);
            parameterTypes.AddNestedComplexTypes(properties, processedTypes);
        }

        return parameterTypes;
    }

    private static void AddNestedComplexTypes(this HashSet<HandlebarsParameterTypeMetadata> parameterTypes, PropertyInfo[] properties, HashSet<Type> processedTypes)
    {
        // Add nested complex types
        foreach (var property in properties)
        {
            // Only convert the property type if we have not already done so.
            if (!processedTypes.Contains(property.PropertyType))
            {
                parameterTypes.UnionWith(property.PropertyType.ToHandlebarsParameterTypeMetadata(processedTypes));
            }
        }
    }

    private static Type GetTypeFromSchema(string schemaType) =>
        schemaType switch
        {
            "string" => typeof(string),
            "integer" => typeof(long),
            "number" => typeof(double),
            "boolean" => typeof(bool),
            "array" => typeof(object[]),
            _ => typeof(object) // default to object for "object", "null", or anything unexpected
        };

    public static KernelParameterMetadata ParseJsonSchema(this KernelParameterMetadata parameter)
    {
        var schema = parameter.Schema!;

        var type = "object";
        if (schema.RootElement.TryGetProperty("type", out var typeNode))
        {
            type = typeNode.Deserialize<string>()!;
        }

        if (IsPrimitiveOrStringType(type) || type == "null")
        {
            return new(parameter)
            {
                ParameterType = GetTypeFromSchema(type),
                Schema = null,
            };
        }

        return parameter;
    }

    public static string ToJsonString(this JsonElement jsonProperties)
    {
        return JsonSerializer.Serialize(jsonProperties, JsonOptionsCache.WriteIndented);
    }

    public static string GetSchemaTypeName(this KernelParameterMetadata parameter)
    {
        var schemaType = parameter.Schema?.RootElement.TryGetProperty("type", out var typeElement) is true ? typeElement.ToString() : "object";
        return $"{parameter.Name}-{schemaType}";
    }

    public static KernelParameterMetadata ToKernelParameterMetadata(this KernelReturnParameterMetadata parameter, string functionName) =>
        new($"{functionName}Returns")
        {
            Description = parameter.Description,
            ParameterType = parameter.ParameterType,
            Schema = parameter.Schema
        };

    public static KernelReturnParameterMetadata ToKernelReturnParameterMetadata(this KernelParameterMetadata parameter) =>
        new()
        {
            Description = parameter.Description,
            ParameterType = parameter.ParameterType,
            Schema = parameter.Schema
        };
}
