// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Text.Json.Nodes;
using System.Web;

namespace Microsoft.SemanticKernel.Plugins.OpenApi;

/// <summary>
/// Serializes REST API operation parameter of the 'Form' style.
/// </summary>
internal static class FormStyleParameterSerializer
{
    /// <summary>
    /// Serializes a REST API operation `Form` style parameter.
    /// </summary>
    /// <param name="parameter">The REST API operation parameter to serialize.</param>
    /// <param name="argument">The parameter argument.</param>
    /// <returns>The serialized parameter.</returns>
    public static string Serialize(RestApiOperationParameter parameter, string argument)
    {
        const string ArrayType = "array";

        Verify.NotNull(parameter);

        if (parameter.Style != RestApiOperationParameterStyle.Form)
        {
            throw new ArgumentException($"Unexpected Rest API operation parameter style - `{parameter.Style}`", nameof(parameter));
        }

        // Handling parameters of array type.
        if (parameter.Type == ArrayType)
        {
            return SerializeArrayParameter(parameter, argument);
        }

        // Handling parameters of primitive - integer, string, etc type.
        return $"{parameter.Name}={HttpUtility.UrlEncode(argument)}";
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
            throw new KernelException($"Can't deserialize parameter name `{parameter.Name}` argument `{argument}` to JSON array");
        }

        if (parameter.Expand)
        {
            return ArrayParameterValueSerializer.SerializeArrayAsSeparateParameters(parameter.Name, array, delimiter: "&"); //id=1&id=2&id=3
        }

        return $"{parameter.Name}={ArrayParameterValueSerializer.SerializeArrayAsDelimitedValues(array, delimiter: ",")}"; //id=1,2,3
    }
}
