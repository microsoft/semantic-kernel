// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;

namespace Microsoft.SemanticKernel.Planning.Handlebars;

internal sealed class HandlebarsParameterTypeView
{
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    [JsonPropertyName("isComplexType")]
    public bool IsComplexType { get; set; } = false;

    /// <summary>
    /// If this is a complex type, this will contain the properties of the complex type.
    /// </summary>
    [JsonPropertyName("properties")]
    public List<ParameterView> Properties { get; set; } = new();
}

internal static class ParameterTypeExtensions
{
    /// <summary>
    /// Converts a type to a data class definition.
    /// Primitive types will stay a primitive type.
    /// Complex types will become a data class.
    /// If there are nested complex types, the nested complex type will also be returned.
    /// Example:
    /// Primitive type:
    /// System.String -> string
    /// Complex type:
    /// class ComplexType:
    ///    propertyA: int
    ///    propertyB: str
    ///    propertyC: PropertyC
    /// </summary>
    public static HashSet<HandlebarsParameterTypeView> ToParameterTypes(this Type type)
    {
        var parameterTypes = new HashSet<HandlebarsParameterTypeView>();

        if (type.IsPrimitive || type == typeof(string))
        {
            // Primitive types and string
            parameterTypes.Add(new HandlebarsParameterTypeView()
            {
                Name = type.Name,
            });
        }
        else if (type.IsEnum)
        {
            // Enum
            parameterTypes.Add(new HandlebarsParameterTypeView()
            {
                Name = type.Name,
            });
        }
        else if (type.IsClass)
        {
            // Class
            var properties = type.GetProperties();

            parameterTypes.Add(new HandlebarsParameterTypeView()
            {
                Name = type.Name,
                IsComplexType = true,
                Properties = properties.Select(p => new ParameterView(p.Name, ParameterType: p.PropertyType)).ToList()
            });

            // Add nested complex types
            foreach (var property in properties)
            {
                var propertyParameterTypes = property.PropertyType.ToParameterTypes();
                foreach (var propertyParameterType in propertyParameterTypes)
                {
                    if (propertyParameterType.IsComplexType)
                    {
                        parameterTypes.Add(propertyParameterType);
                    }
                }
            }
        }

        return parameterTypes;
    }
}
