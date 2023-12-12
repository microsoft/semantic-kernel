// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text.Json;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Provides functionality for converting OpenApi types - https://swagger.io/docs/specification/data-models/data-types/
/// </summary>
internal static class OpenApiTypeConverter
{
    /// <summary>
    /// Converts the given parameter argument to a JsonNode based on the specified type.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value.</returns>
    public static JsonNode Convert(string name, string type, object argument)
    {
        Verify.NotNull(argument);

        try
        {
            if (s_converters.TryGetValue(type, out var converter))
            {
                var result = converter(argument);
                return result is null
                    ? throw new ArgumentOutOfRangeException(name, argument, $"Argument type '{argument.GetType()}' is not convertible to parameter type '{type}'.")
                    : result;
            }

            throw new NotSupportedException($"Unexpected type '{type}' of parameter '{name}' with argument '{argument}'.");
        }
        catch (ArgumentException ex)
        {
            throw new ArgumentOutOfRangeException(name, argument, ex.Message);
        }
        catch (FormatException ex)
        {
            throw new ArgumentOutOfRangeException(name, argument, ex.Message);
        }
    }

    /// <summary>
    /// Converts the given argument to a JsonNode of type string.
    /// </summary>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertString(object argument)
    {
        return JsonValue.Create(argument);
    }

    /// <summary>
    /// Converts the given argument to a JsonNode of type array.
    /// </summary>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertArray(object argument)
    {
        return argument switch
        {
            string s => JsonArray.Parse(s) as JsonArray,
            _ => JsonSerializer.SerializeToNode(argument) as JsonArray
        };
    }

    /// <summary>
    /// Converts the given argument to a JsonNode of type integer.
    /// </summary>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertInteger(object argument)
    {
        return argument switch
        {
            string stringArgument => JsonValue.Create(long.Parse(stringArgument, CultureInfo.InvariantCulture)),
            byte or sbyte or short or ushort or int or uint or long or ulong => JsonValue.Create(argument),
            _ => null
        };
    }

    /// <summary>
    /// Converts the given argument to a JsonNode of type boolean.
    /// </summary>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertBoolean(object argument)
    {
        return argument switch
        {
            bool b => JsonValue.Create(b),
            string s => JsonValue.Create(bool.Parse(s)),
            _ => null
        };
    }

    /// <summary>
    /// Converts the given argument to a JsonNode of type number.
    /// </summary>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertNumber(object argument)
    {
        return argument switch
        {
            string stringArgument when long.TryParse(stringArgument, out var intValue) => JsonValue.Create(intValue),
            string stringArgument when double.TryParse(stringArgument, out var doubleValue) => JsonValue.Create(doubleValue),
            byte or sbyte or short or ushort or int or uint or long or ulong or float or double or decimal => JsonValue.Create(argument),
            _ => null
        };
    }

    /// <summary>
    /// A dictionary mapping OpenApi types to their respective converter functions.
    /// </summary>
    private static readonly Dictionary<string, Func<object, JsonNode?>> s_converters = new()
    {
        { "number", ConvertNumber },
        { "boolean", ConvertBoolean },
        { "integer", ConvertInteger },
        { "array", ConvertArray },
        { "string", ConvertString }
    };
}
