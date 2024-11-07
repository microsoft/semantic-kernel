// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Serializes REST API parameter of the 'PipeDelimited' style.
/// </summary>
internal static class PipeDelimitedStyleParameterSerializer
{
    /// <summary>
    /// Serializes a REST API `PipeDelimited` style parameter.
    /// </summary>
    /// <param name="parameter">The REST API parameter to serialize.</param>
    /// <param name="argument">The parameter argument.</param>
    /// <returns>The serialized parameter.</returns>
    public static string Serialize(RestApiParameter parameter, JsonNode argument)
    {
        const string ArrayType = "array";

        Verify.NotNull(parameter);
        Verify.NotNull(argument);

        if (parameter.Style != RestApiParameterStyle.PipeDelimited)
        {
            throw new NotSupportedException($"Unsupported Rest API parameter style '{parameter.Style}' for parameter '{parameter.Name}'");
        }

        if (parameter.Type != ArrayType)
        {
            throw new NotSupportedException($"Unsupported Rest API parameter type '{parameter.Type}' for parameter '{parameter.Name}'");
        }

        return SerializeArrayParameter(parameter, argument);
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
            return ArrayParameterValueSerializer.SerializeArrayAsSeparateParameters(parameter.Name, array, delimiter: "&"); //id=1&id=2&id=3
        }

        return $"{parameter.Name}={ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: "|")}"; //id=1|2|3
    }
}
