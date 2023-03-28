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
    /// Retrieve one or more values from a JSON string using a JsonPath query.
    /// </summary>
    [SKFunction("Retrieve a single value of a property from a JSON string.")]
    [SKFunctionInput(Description = "JSON string")]
    [SKFunctionContextParameter(Name = "JsonPath", Description = "JSON path.")]
    public string GetJsonPropertyValue(string json, SKContext context)
    {
        if (string.IsNullOrWhiteSpace(json))
        {
            context.Fail($"Missing input JSON.");
            return string.Empty;
        }

        if (!context.Variables.Get(Parameters.JsonPath, out string jsonPath))
        {
            context.Fail($"Missing variable {Parameters.JsonPath}.");
            return string.Empty;
        }

        JObject jsonObject = JObject.Parse(json);

        JToken[] tokens = jsonObject.SelectTokens(jsonPath).ToArray();

        if (!tokens.Any())
        {
            // If there were no results, return an empty string.
            return string.Empty;
        }
        else if (tokens.Length == 1 &&
            tokens.First().GetType() == typeof(JValue))
        {
            // If there was a single result that is a simple value, return just that value.
            return tokens.First().Value<string>() ?? string.Empty;
        }
        else 
        {
            // Anything else, reserialize the results as structured JSON.
            return JsonConvert.SerializeObject(tokens, Formatting.None);
        }
    }
}
