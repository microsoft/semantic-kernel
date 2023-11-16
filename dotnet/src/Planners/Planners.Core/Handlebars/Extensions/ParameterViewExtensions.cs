// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Planners.Handlebars.Models;

namespace Microsoft.SemanticKernel.Planners.Handlebars.Extensions;

internal static class ParameterViewExtensions
{
    /// <summary>
    /// Checks if type is primitive or string
    /// </summary>
    public static bool isPrimitiveOrStringType(Type type) => type.IsPrimitive || type == typeof(string);

    /// <summary>
    /// Converts non-primitive types to a data class definition and returns a hash set of complex type view definitions.
    /// Complex types will become a data class.
    /// If there are nested complex types, the nested complex type will also be returned.
    /// Example:
    /// Complex type:
    /// class ComplexType:
    ///    propertyA: int
    ///    propertyB: str
    ///    propertyC: PropertyC
    /// </summary>
    public static HashSet<HandlebarsParameterTypeView> ToHandlebarsParameterTypeView(this Type type)
    {
        var parameterTypes = new HashSet<HandlebarsParameterTypeView>();
        if (type.IsGenericType && type.GetGenericTypeDefinition() == typeof(Task<>))
        {
            // Async return type - need to extract the actual return type
            var actualReturnType = type.GenericTypeArguments[0]; // Actual Return Type
            var returnTypeProperties = actualReturnType.GetProperties();

            if (!isPrimitiveOrStringType(actualReturnType) && returnTypeProperties.Length is not 0)
            {
                parameterTypes.Add(new HandlebarsParameterTypeView()
                {
                    Name = actualReturnType.Name,
                    IsComplexType = true,
                    Properties = returnTypeProperties.Select(p => new ParameterView(p.Name, ParameterType: p.PropertyType)).ToList()
                });

                parameterTypes.AddNestedComplexTypes(returnTypeProperties);
            }
        }
        else if (type.IsClass && type != typeof(string))
        {
            // Class
            var properties = type.GetProperties();

            parameterTypes.Add(new HandlebarsParameterTypeView()
            {
                Name = type.Name,
                IsComplexType = properties.Length is not 0,
                Properties = properties.Select(p => new ParameterView(p.Name, ParameterType: p.PropertyType)).ToList()
            });

            parameterTypes.AddNestedComplexTypes(properties);
        }

        return parameterTypes;
    }

    private static void AddNestedComplexTypes(this HashSet<HandlebarsParameterTypeView> parameterTypes, PropertyInfo[] properties)
    {
        // Add nested complex types
        foreach (var property in properties)
        {
            parameterTypes.UnionWith(property.PropertyType.ToHandlebarsParameterTypeView());
        }
    }

    public static bool isPrimitiveOrStringType(string type) =>
        type == "string" || type == "number" || type == "integer" || type == "boolean" || type == "null";

    private static Type GetTypeFromSchema(string schemaType)
    {
        var typeMap = new Dictionary<string, Type>
            {
                {"string", typeof(string)},
                {"integer", typeof(long)},
                {"number", typeof(double)},
                {"boolean", typeof(bool)},
                {"object", typeof(object)},
                {"array", typeof(object[])}
            };

        return typeMap[schemaType];
    }

    public static ParameterView ParseJsonSchema(this ParameterView parameter)
    {
        var schema = parameter.Schema!;
        var type = schema.RootElement.GetProperty("type").GetString() ?? "object";
        if (isPrimitiveOrStringType(type))
        {
            return parameter with { ParameterType = GetTypeFromSchema(type), Schema = null };
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

    public static string GetSchemaTypeName(this ParameterView parameter)
    {
        var schemaType = parameter.Schema is not null && parameter.Schema.RootElement.TryGetProperty("type", out var typeElement) ? typeElement.ToString() : "object";
        return $"{parameter.Name}-{schemaType}";
    }

    public static ParameterView ToParameterView(this ReturnParameterView parameter, string functionName) => new($"{functionName}Returns", parameter.Description, ParameterType: parameter.ParameterType, Schema: parameter.Schema);

    public static ReturnParameterView ToReturnParameterView(this ParameterView parameter) => new(parameter.Description, ParameterType: parameter.ParameterType, Schema: parameter.Schema);
}
