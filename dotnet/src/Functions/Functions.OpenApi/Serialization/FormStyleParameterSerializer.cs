// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using System.Web;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Serializes REST API parameter of the 'Form' style.
/// </summary>
internal static class FormStyleParameterSerializer
{
    /// <summary>
    /// Serializes a REST API `Form` style parameter.
    /// </summary>
    /// <param name="parameter">The REST API parameter to serialize.</param>
    /// <param name="argument">The parameter argument.</param>
    /// <returns>The serialized parameter.</returns>
    public static string Serialize(RestApiParameter parameter, JsonNode argument)
    {
        const string ArrayType = "array";

        Verify.NotNull(parameter);
        Verify.NotNull(argument);

        var style = parameter.Style ?? RestApiParameterStyle.Form;
        if (style != RestApiParameterStyle.Form)
        {
            throw new NotSupportedException($"Unsupported Rest API parameter style '{parameter.Style}' for parameter '{parameter.Name}'");
        }

        // Handling parameters of array type.
        if (parameter.Type == ArrayType)
        {
            return SerializeArrayParameter(parameter, argument);
        }

        // Handling parameters where the underlying value is already a string.
        if (argument is JsonValue jsonValue && jsonValue.TryGetValue(out string? value))
        {
            return $"{parameter.Name}={HttpUtility.UrlEncode(value)}";
        }

        // Handling parameters of any arbitrary type by using JSON format without enclosing quotes.
        return $"{parameter.Name}={HttpUtility.UrlEncode(argument.ToString().Trim('"'))}";
    }

    /// <summary>
    /// Serializes an array-type parameter.
    /// </summary>
    /// <param name="parameter">The REST API parameter to serialize.</param>
    /// <param name="argument">The argument value.</param>
    /// <returns>The serialized parameter string.</returns>
    private static string SerializeArrayParameter(RestApiParameter parameter, JsonNode argument)
    {
        if (argument is not JsonArray array)
        {
            throw new ArgumentException(parameter.Name, $"Unexpected argument type '{argument.GetType()} with value '{argument}' for parameter type '{parameter.Type}'.");
        }

        if (parameter.Expand)
        {
            return ArrayParameterValueSerializer.SerializeArrayAsSeparateParameters(parameter.Name, array, delimiter: "&"); // id=1&id=2&id=3
        }

        return $"{parameter.Name}={ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: ",")}"; // id=1,2,3
    }
}
