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
                var result = converter(name, type, argument);
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
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertString(string name, string type, object argument)
    {
        return JsonValue.Create(argument);
    }

    /// <summary>
    /// Converts the given argument to a JsonNode of type array.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertArray(string name, string type, object argument)
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
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertInteger(string name, string type, object argument)
    {
        return argument switch
        {
            byte b => JsonValue.Create(b),
            sbyte sb => JsonValue.Create(sb),
            short sh => JsonValue.Create(sh),
            ushort ush => JsonValue.Create(ush),
            int i => JsonValue.Create(i),
            uint ui => JsonValue.Create(ui),
            long l => JsonValue.Create(l),
            ulong ul => JsonValue.Create(ul),
            string s => JsonValue.Create(long.Parse(s, CultureInfo.InvariantCulture)),
            _ => null
        };
    }

    /// <summary>
    /// Converts the given argument to a JsonNode of type boolean.
    /// </summary>
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertBoolean(string name, string type, object argument)
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
    /// <param name="name">The parameter name.</param>
    /// <param name="type">The parameter type.</param>
    /// <param name="argument">The argument to be converted.</param>
    /// <returns>A JsonNode representing the converted value, or null if the argument cannot be converted.</returns>
    private static JsonNode? ConvertNumber(string name, string type, object argument)
    {
        return argument switch
        {
            byte b => JsonValue.Create(b),
            sbyte sb => JsonValue.Create(sb),
            short sh => JsonValue.Create(sh),
            ushort ush => JsonValue.Create(ush),
            int i => JsonValue.Create(i),
            uint ui => JsonValue.Create(ui),
            long l => JsonValue.Create(l),
            ulong ul => JsonValue.Create(ul),
            float f => JsonValue.Create(f),
            double d => JsonValue.Create(d),
            decimal d => JsonValue.Create(d),
            string s when long.TryParse(s, out var intValue) => JsonValue.Create(intValue),
            string s => JsonValue.Create(double.Parse(s, CultureInfo.InvariantCulture)),
            _ => null
        };
    }

    /// <summary>
    /// A dictionary mapping OpenApi types to their respective converter functions.
    /// </summary>
    private static readonly Dictionary<string, Func<string, string, object, JsonNode?>> s_converters = new()
    {
        { "number", ConvertNumber },
        { "boolean", ConvertBoolean },
        { "integer", ConvertInteger },
        { "array", ConvertArray },
        { "string", ConvertString }
    };
}
