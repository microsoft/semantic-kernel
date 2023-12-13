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
    public static string Serialize(RestApiOperationParameter parameter, string argument)
    {
        const string ArrayType = "array";

        Verify.NotNull(parameter);

        if (parameter.Style != RestApiOperationParameterStyle.Simple)
        {
            throw new ArgumentException($"Unexpected Rest API operation parameter style - `{parameter.Style}`", nameof(parameter));
        }

        // Serializing parameters of array type.
        if (parameter.Type == ArrayType)
        {
            return SerializeArrayParameter(parameter, argument);
        }

        // Serializing parameters of primitive - integer, string, etc type.
        return argument;
    }

    /// <summary>
    /// Serializes an array-type parameter.
    /// </summary>
    /// <param name="parameter">The REST API operation parameter to serialize.</param>
    /// <param name="argument">The argument value.</param>
    /// <returns>The serialized parameter string.</returns>
    private static string SerializeArrayParameter(RestApiOperationParameter parameter, string argument)
    {
        if (JsonNode.Parse(argument) is not JsonArray array)
        {
            throw new KernelException($"Can't deserialize parameter name '{parameter.Name}' argument '{argument}' to JSON array.");
        }

        return ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: ",", encode: false); //1,2,3
    }
}
