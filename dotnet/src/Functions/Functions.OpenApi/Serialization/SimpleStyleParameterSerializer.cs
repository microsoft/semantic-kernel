// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Serializes REST API operation parameter of the 'Simple' style.
/// </summary>
internal static class SimpleStyleParameterSerializer
{
    /// <summary>
    /// Serializes a REST API operation `Simple` style parameter.
    /// </summary>
    /// <param name="parameter">The REST API operation parameter to serialize.</param>
    /// <param name="argument">The parameter argument.</param>
    /// <returns>The serialized parameter.</returns>
    public static string Serialize(RestApiOperationParameter parameter, JsonNode argument)
    {
        const string ArrayType = "array";

        Verify.NotNull(parameter);
        Verify.NotNull(argument);

        if (parameter.Style != RestApiOperationParameterStyle.Simple)
        {
            throw new NotSupportedException($"Unsupported Rest API operation parameter style '{parameter.Style}' for parameter '{parameter.Name}'");
        }

        // Serializing parameters of array type.
        if (parameter.Type == ArrayType)
        {
            return SerializeArrayParameter(parameter, argument);
        }

        // Handling parameters of primitive and removing extra quotes added by the JsonValue for string values.
        return argument.ToString().Trim('"');
    }

    /// <summary>
    /// Serializes an array-type parameter.
    /// </summary>
    /// <param name="parameter">The REST API operation parameter to serialize.</param>
    /// <param name="argument">The argument value.</param>
    /// <returns>The serialized parameter string.</returns>
    private static string SerializeArrayParameter(RestApiOperationParameter parameter, object argument)
    {
        if (argument is not JsonArray array)
        {
            throw new ArgumentException(parameter.Name, $"Unexpected argument type '{argument.GetType()} with value '{argument}' for parameter type '{parameter.Type}'.");
        }

        return ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: ",", encode: false); //1,2,3
    }
}
