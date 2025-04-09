// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Serializes REST API parameter of the 'Simple' style.
/// </summary>
internal static class SimpleStyleParameterSerializer
{
    /// <summary>
    /// Serializes a REST API `Simple` style parameter.
    /// </summary>
    /// <param name="parameter">The REST API parameter to serialize.</param>
    /// <param name="argument">The parameter argument.</param>
    /// <returns>The serialized parameter.</returns>
    public static string Serialize(RestApiParameter parameter, JsonNode argument)
    {
        const string ArrayType = "array";

        Verify.NotNull(parameter);
        Verify.NotNull(argument);

        var style = parameter.Style ?? RestApiParameterStyle.Simple;
        if (style != RestApiParameterStyle.Simple)
        {
            throw new NotSupportedException($"Unsupported Rest API parameter style '{parameter.Style}' for parameter '{parameter.Name}'");
        }

        // Serializing parameters of array type.
        if (parameter.Type == ArrayType)
        {
            return SerializeArrayParameter(parameter, argument);
        }

        // Handling parameters where the underlying value is already a string.
        if (argument is JsonValue jsonValue && jsonValue.TryGetValue(out string? value))
        {
            return value;
        }

        // Handling parameters of any arbitrary type by using JSON format without enclosing quotes.
        return argument.ToString().Trim('"');
    }

    /// <summary>
    /// Serializes an array-type parameter.
    /// </summary>
    /// <param name="parameter">The REST API parameter to serialize.</param>
    /// <param name="argument">The argument value.</param>
    /// <returns>The serialized parameter string.</returns>
    private static string SerializeArrayParameter(RestApiParameter parameter, object argument)
    {
        if (argument is not JsonArray array)
        {
            throw new ArgumentException(parameter.Name, $"Unexpected argument type '{argument.GetType()} with value '{argument}' for parameter type '{parameter.Type}'.");
        }

        return ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: ",", encode: false); //1,2,3
    }
}
