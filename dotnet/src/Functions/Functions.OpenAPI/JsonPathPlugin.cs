// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Microsoft.SemanticKernel.Functions.OpenAPI;

/// <summary>
/// Provides methods to retrieve JSON elements from a JSON string using JsonPath queries.
/// </summary>
public sealed class JsonPathPlugin
{
    /// <summary>
    /// <see cref="ContextVariables"/> parameter names.
    /// </summary>
    public static class Parameters
    {
        /// <summary>
        /// JSON path.
        /// </summary>
        public const string JsonPath = "jsonpath";
    }

    /// <summary>
    /// Retrieve the value of a JSON element from a JSON string using a JsonPath query.
    /// </summary>
    /// <param name="json">The JSON string to query.</param>
    /// <param name="jsonPath">The JsonPath query to use.</param>
    /// <returns>The value of the JSON element as a string.</returns>
    /// <exception cref="ArgumentException">Thrown when the provided JSON string is null or whitespace.</exception>
    [SKFunction, Description("Retrieve the value of a JSON element from a JSON string using a JsonPath query.")]
    public string GetJsonElementValue(
        [Description("JSON string")] string json,
        [Description("JSON path query.")] string jsonPath)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            throw new ArgumentException("Variable was null or whitespace", nameof(json));
        }

        JObject jsonObject = JObject.Parse(json);

        JToken? token = jsonObject.SelectToken(jsonPath);

        return token?.Value<string>() ?? string.Empty;
    }

    /// <summary>
    /// Retrieve a collection of JSON elements from a JSON string using a JsonPath query.
    /// </summary>
    /// <param name="json">The JSON string to query.</param>
    /// <param name="jsonPath">The JsonPath query to use.</param>
    /// <returns>A JSON string representing the collection of JSON elements.</returns>
    /// <exception cref="ArgumentException">Thrown when the provided JSON string is null or whitespace.</exception>
    [SKFunction, Description("Retrieve a collection of JSON elements from a JSON string using a JsonPath query.")]
    public string GetJsonElements(
        [Description("JSON string")] string json,
        [Description("JSON path query.")] string jsonPath)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            throw new ArgumentException("Variable was null or whitespace", nameof(json));
        }

        JObject jsonObject = JObject.Parse(json);

        JToken[] tokens = jsonObject.SelectTokens(jsonPath).ToArray();

        return JsonConvert.SerializeObject(tokens, Formatting.None);
    }
}
