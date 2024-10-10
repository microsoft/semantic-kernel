// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
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
        [JsonPropertyName("parameters")]
        [JsonPropertyOrder(1)]
        [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
        public List<InputParameter> Parameters { get; set; } = new();
    }

    /// <summary>
    /// AI service configuration
    /// </summary>
    public class ServiceConfig
    {
        /// <summary>
        /// Model ID in AI service provider (e.g. text-davinci-003).
        /// </summary>
        [JsonPropertyName("model_id")]
        [JsonPropertyOrder(1)]
        public string ModelId { get; set; } = string.Empty;

        /// <summary>
        /// Service priority order. Kernel will check all registered services and choose one with highest priority order.
        /// </summary>
        [JsonPropertyName("order")]
        [JsonPropertyOrder(3)]
        public int Order { get; set; }

        /// <summary>
        /// Dynamic settings, specific to AI model.
        /// </summary>
        [JsonPropertyName("settings")]
        [JsonPropertyOrder(4)]
        public JsonObject Settings { get; set; } = new();
    }

    /// <summary>
    /// Description
    /// </summary>
    [JsonPropertyName("description")]
    [JsonPropertyOrder(1)]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Input configuration (that is, list of all input parameters).
    /// </summary>
    [JsonPropertyName("input")]
    [JsonPropertyOrder(2)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public InputConfig Input { get; set; } = new();

    /// <summary>
    /// Default settings for AI model.
    /// Will be used when there is no matching AI service in configuration, which is registered in kernel.
    /// </summary>
    [JsonPropertyName("default_settings")]
    [JsonPropertyOrder(3)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public JsonObject DefaultSettings { get; set; } = new();

    /// <summary>
    /// Default AI services to use.
    /// </summary>
    [JsonPropertyName("services")]
    [JsonPropertyOrder(4)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<ServiceConfig> Services { get; set; } = new();

    /// <summary>
    /// Creates a prompt template configuration from JSON.
    /// </summary>
    /// <param name="json">JSON of the prompt template configuration.</param>
    /// <returns>Prompt template configuration.</returns>
    public static PromptTemplateConfig FromJson(string json)
    {
        var result = Json.Deserialize<PromptTemplateConfig>(json);

        if (result is null)
        {
            throw new ArgumentException("Unable to deserialize prompt template config from argument. The deserialization returned null.", nameof(json));
        }

        return result;
    }
}
