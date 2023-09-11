// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Dynamic;
using System.Text.Json;
using System.Text.RegularExpressions;

namespace Microsoft.SemanticKernel.Text;

/// <summary>
/// Extension methods to convert a JsonElement to an Expando
/// </summary>
internal static class JsonElementExtensions
{
    // Method to convert a JsonElement to an Expando object
    internal static ExpandoObject ToExpando(this JsonElement jsonElement, bool snakeToPascal = true)
    {
        // Create a new Expando object
        ExpandoObject expando = new();

        // Get the dictionary of the Expando object
        IDictionary<string, object> expandoDict = expando;

        // Iterate over the properties and values of the JsonElement
        foreach (JsonProperty property in jsonElement.EnumerateObject())
        {
            // Get the property name and value
            string name = property.Name;
            if (snakeToPascal)
            {
                name = SnakeToPascal(name);
            }
            JsonElement value = property.Value;

            // Check the value type and add it to the Expando object accordingly
            switch (value.ValueKind)
            {
                case JsonValueKind.Object:
                    // If the value is an object, recursively convert it to an Expando object
                    expandoDict.Add(name, ToExpando(value));
                    break;
                case JsonValueKind.Array:
                    // If the value is an array, convert it to a list of objects
                    List<object> list = new();
                    foreach (JsonElement element in value.EnumerateArray())
                    {
                        // If the element is an object, recursively convert it to an Expando object
                        if (element.ValueKind == JsonValueKind.Object)
                        {
                            list.Add(ToExpando(element));
                        }
                        else
                        {
                            // Otherwise, add the element value directly
                            list.Add(element.GetValue());
                        }
                    }
                    expandoDict.Add(name, list);
                    break;
                default:
                    // For other value types, add the value directly
                    expandoDict.Add(name, value.GetValue());
                    break;
            }
        }

        // Return the Expando object
        return expando;
    }

    // Extension method to get the value of a JsonElement based on its type
    public static object? GetValue(this JsonElement jsonElement)
    {
        switch (jsonElement.ValueKind)
        {
            case JsonValueKind.String:
                return jsonElement.GetString();
            case JsonValueKind.Number:
                return jsonElement.GetDouble();
            case JsonValueKind.True:
                return true;
            case JsonValueKind.False:
                return false;
            case JsonValueKind.Null:
                return null;
            default:
                throw new InvalidOperationException($"Unsupported value kind: {jsonElement.ValueKind}");
        }
    }

    private static string SnakeToPascal(string name)
    {
        // If the input is null or empty, return it as it is
        if (string.IsNullOrEmpty(name))
        {
            return name;
        }

        // Use a regular expression to match the name case pattern: one or more lowercase letters followed by an optional underscore
        var pattern = @"[a-z]+_?";

        // Use a match evaluator to replace each match with the capitalized version of the first letter and the rest of the letters without the underscore
        var evaluator = new MatchEvaluator(m => char.ToUpper(m.Value[0]) + m.Value.Substring(1).TrimEnd('_'));

        // Return the modified string
        return Regex.Replace(name, pattern, evaluator);
    }
}
