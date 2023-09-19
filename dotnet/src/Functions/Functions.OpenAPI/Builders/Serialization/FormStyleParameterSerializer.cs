// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Web;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Functions.OpenAPI.Model;

namespace Microsoft.SemanticKernel.Functions.OpenAPI.Builders.Serialization;

/// <summary>
/// Serializes REST API operation parameter of the 'Form' style.
/// </summary>
internal class FormStyleParameterSerializer
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

        if (parameter is null)
        {
            throw new ArgumentNullException(nameof(parameter));
        }

        if (parameter.Style != RestApiOperationParameterStyle.Form)
        {
            throw new SKException($"Unexpected Rest Api operation parameter style - `{parameter.Style}`");
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
            throw new SKException($"Can't deserialize parameter name `{parameter.Name}` argument `{argument}` to JSON array");
        }

        if (parameter.Explode)
        {
            return SerializeArrayItemsAsSeparateParameters(parameter.Name, array);              //id=1&id=2&id=3
        }

        return SerializeArrayItemsAsParameterWithCommaSeparatedValues(parameter.Name, array);   //id=1,2,3
    }

    /// <summary>
    /// Serializes the items of an array as separate parameters with the same name.
    /// </summary>
    /// <param name="name">The name of the parameter.</param>
    /// <param name="array">The array containing the items to be serialized.</param>
    /// <returns>A string containing the serialized parameters.</returns>
    private static string SerializeArrayItemsAsSeparateParameters(string name, JsonArray array)
    {
        var segments = new List<string>();

        foreach (var item in array)
        {
            segments.Add($"{name}={HttpUtility.UrlEncode(item?.ToString())}");
        }

        return string.Join("&", segments); ; //id=1&id=2&id=3
    }

    /// <summary>
    /// Serializes the items of an array as a single parameter with comma-separated values.
    /// </summary>
    /// <param name="name">The name of the parameter.</param>
    /// <param name="array">The array containing the items to be serialized.</param>
    /// <returns>A string containing the serialized parameter in the format "name=item1,item2,...".</returns>
    private static string SerializeArrayItemsAsParameterWithCommaSeparatedValues(string name, JsonArray array)
    {
        const string ValuesSeparator = ",";

        var values = new List<string>();

        foreach (var item in array)
        {
            values.Add(HttpUtility.UrlEncode(item?.ToString()));
        }

        return $"{name}={string.Join(ValuesSeparator, values)}"; //id=1,2,3
    }
}
