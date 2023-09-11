// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.SemanticFunctions;

/// <summary>
/// Prompt template configuration.
/// </summary>
public class PromptTemplateConfig
{
    /// <summary>
    /// Input parameter for semantic functions.
    /// </summary>
    public class InputParameter
    {
        /// <summary>
        /// Name of the parameter to pass to the function.
        /// e.g. when using "{{$input}}" the name is "input", when using "{{$style}}" the name is "style", etc.
        /// </summary>
        [JsonPropertyName("name")]
        [JsonPropertyOrder(1)]
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Parameter description for UI apps and planner. Localization is not supported here.
        /// </summary>
        [JsonPropertyName("description")]
        [JsonPropertyOrder(2)]
        public string Description { get; set; } = string.Empty;

        /// <summary>
        /// Default value when nothing is provided.
        /// </summary>
        [JsonPropertyName("defaultValue")]
        [JsonPropertyOrder(3)]
        public string DefaultValue { get; set; } = string.Empty;
    }

    /// <summary>
    /// Input configuration (list of all input parameters for a semantic function).
    /// </summary>
    public class InputConfig
    {
        /// <summary>
        /// Gets or sets the list of input parameters.
        /// </summary>
        [JsonPropertyName("parameters")]
        [JsonPropertyOrder(1)]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<InputParameter> Parameters { get; set; } = new();
    }

    /// <summary>
    /// Schema - Not currently used.
    /// </summary>
    [JsonPropertyName("schema")]
    [JsonPropertyOrder(1)]
    public int Schema { get; set; } = 1;

    /// <summary>
    /// Type, such as "completion", "embeddings", etc.
    /// </summary>
    /// <remarks>TODO: use enum</remarks>
    [JsonPropertyName("type")]
    [JsonPropertyOrder(2)]
    public string Type { get; set; } = "completion";

    /// <summary>
    /// Description
    /// </summary>
    [JsonPropertyName("description")]
    [JsonPropertyOrder(3)]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Completion configuration parameters.
    /// </summary>
    [JsonPropertyName("completion")]
    [JsonPropertyOrder(4)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public dynamic? Completion { get; set; }

    /// <summary>
    /// Default AI services to use.
    /// </summary>
    [JsonPropertyName("default_services")]
    [JsonPropertyOrder(5)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<string> DefaultServices { get; set; } = new();

    /// <summary>
    /// Input configuration (that is, list of all input parameters).
    /// </summary>
    [JsonPropertyName("input")]
    [JsonPropertyOrder(6)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public InputConfig Input { get; set; } = new();

    /// <summary>
    /// Return the service id
    /// </summary>
    internal string? GetServiceId()
    {
        if (this.Completion is null)
        {
            return null;
        }

        if (this.Completion.GetType() == typeof(JsonElement))
        {
            var jsonElement = (JsonElement)this.Completion;
            if (jsonElement.TryGetProperty("service_id", out var value1))
            {
                return value1.GetString();
            }
            if (jsonElement.TryGetProperty("ServiceId", out var value2))
            {
                return value2.GetString();
            }
            return null;
        }

        string? serviceId = DynamicUtils.TryGetPropertyValue<string?>(this.Completion, "service_id", null);
        if (serviceId is null)
        {
            serviceId = DynamicUtils.TryGetPropertyValue<string?>(this.Completion, "ServiceId", null);
        }

        return serviceId;
    }

    /// <summary>
    /// Creates a prompt template configuration from JSON.
    /// </summary>
    /// <param name="json">JSON of the prompt template configuration.</param>
    /// <returns>Prompt template configuration.</returns>
    /// <exception cref="ArgumentException">Thrown when the deserialization returns null.</exception>
    public static PromptTemplateConfig FromJson(string json)
    {
        var result = Json.Deserialize<PromptTemplateConfig>(json);
        return result ?? throw new ArgumentException("Unable to deserialize prompt template config from argument. The deserialization returned null.", nameof(json));
    }
}
