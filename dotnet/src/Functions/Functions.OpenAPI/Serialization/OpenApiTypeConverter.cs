// Copyright (c) Microsoft. All rights reserved.

using System.Text.Json.Nodes;
using System.Globalization;
using System.Text.Json;
using System;

namespace Microsoft.SemanticKernel.Plugins.OpenApi.Serialization;

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
            // Converting string to target type.
            if (argument is string stringValue)
            {
                return type switch
                {
                    "number" => long.TryParse(stringValue, out var intValue) ? JsonValue.Create(intValue) : JsonValue.Create(double.Parse(stringValue, CultureInfo.InvariantCulture)),
                    "boolean" => JsonValue.Create(bool.Parse(stringValue)),
                    "integer" => JsonValue.Create(long.Parse(stringValue, CultureInfo.InvariantCulture)),
                    "array" => JsonArray.Parse(stringValue) as JsonArray ?? throw new KernelException($"Unexpected argument '{argument}' for parameter '{name}' of type '{type}'."),
                    "string" => JsonValue.Create(stringValue),
                    _ => throw new NotSupportedException($"Unexpected type '{type}' of parameter '{name}' with argument '{argument}'.")
                };
            }

            // Converting collection to JSON array.
            if (type == "array")
            {
                return JsonSerializer.SerializeToNode(argument)
                    ?? throw new ArgumentOutOfRangeException(name, argument, $"Can't convert argument of '{type}' to JsonArray.");
            }

            // Converting the rest of the types.
            // TODO: Add type checks for the rest of the types.
            var node = JsonValue.Create(argument);

            return node ?? throw new ArgumentOutOfRangeException(name, argument, $"Can't convert argument of '{argument.GetType()}' to JsonValue.");
        }
        catch (FormatException ex)
        {
            throw new ArgumentOutOfRangeException(name, argument, ex.Message);
        }
    }
}
