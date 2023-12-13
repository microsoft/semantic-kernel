// Copyright (c) Microsoft. All rights reserved.

using System;
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
            JsonNode? converter = type switch
            {
                "string" => JsonValue.Create(argument),
                "array" => argument switch
                {
                    string s => JsonArray.Parse(s) as JsonArray,
                    _ => JsonSerializer.SerializeToNode(argument) as JsonArray
                },
                "integer" => argument switch
                {
                    string stringArgument => JsonValue.Create(long.Parse(stringArgument, CultureInfo.InvariantCulture)),
                    byte or sbyte or short or ushort or int or uint or long or ulong => JsonValue.Create(argument),
                    _ => null
                },
                "boolean" => argument switch
                {
                    bool b => JsonValue.Create(b),
                    string s => JsonValue.Create(bool.Parse(s)),
                    _ => null
                },
                "number" => argument switch
                {
                    string stringArgument when long.TryParse(stringArgument, out var intValue) => JsonValue.Create(intValue),
                    string stringArgument when double.TryParse(stringArgument, out var doubleValue) => JsonValue.Create(doubleValue),
                    byte or sbyte or short or ushort or int or uint or long or ulong or float or double or decimal => JsonValue.Create(argument),
                    _ => null
                },
                _ => throw new NotSupportedException($"Unexpected type '{type}' of parameter '{name}' with argument '{argument}'."),
            };

            return converter ?? throw new ArgumentOutOfRangeException(name, argument, $"Argument type '{argument.GetType()}' is not convertible to parameter type '{type}'.");
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
}
