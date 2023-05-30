// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;

namespace Microsoft.SemanticKernel.Skills.OpenAPI;

public class JsonPathSkill
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
    [SKFunction("Retrieve the value of a JSON element from a JSON string using a JsonPath query.")]
    [SKFunctionInput(Description = "JSON string")]
    [SKFunctionContextParameter(Name = "JsonPath", Description = "JSON path query.")]
    public string GetJsonElementValue(string json, SKContext context)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            context.Fail("Missing input JSON.");
            return string.Empty;
        }

        if (!context.Variables.TryGetValue(Parameters.JsonPath, out string? jsonPath))
        {
            context.Fail($"Missing variable {Parameters.JsonPath}.");
            return string.Empty;
        }

        JObject jsonObject = JObject.Parse(json);

        JToken? token = jsonObject.SelectToken(jsonPath);

        return token?.Value<string>() ?? string.Empty;
    }

    /// <summary>
    /// Retrieve a collection of JSON elements from a JSON string using a JsonPath query.
    /// </summary>
    [SKFunction("Retrieve a collection of JSON elements from a JSON string using a JsonPath query.")]
    [SKFunctionInput(Description = "JSON string")]
    [SKFunctionContextParameter(Name = "JsonPath", Description = "JSON path query.")]
    public string GetJsonElements(string json, SKContext context)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            context.Fail("Missing input JSON.");
            return string.Empty;
        }

        if (!context.Variables.TryGetValue(Parameters.JsonPath, out string? jsonPath))
        {
            context.Fail($"Missing variable {Parameters.JsonPath}.");
            return string.Empty;
        }

        JObject jsonObject = JObject.Parse(json);

        JToken[] tokens = jsonObject.SelectTokens(jsonPath).ToArray();

        return JsonConvert.SerializeObject(tokens, Formatting.None);
    }
}
