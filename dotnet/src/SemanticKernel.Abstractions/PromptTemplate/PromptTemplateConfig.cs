// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Models;
using Microsoft.SemanticKernel.Text;

#pragma warning disable IDE0130 // Namespace does not match folder structure

namespace Microsoft.SemanticKernel;

/// <summary>
/// Prompt template configuration.
/// </summary>
public class PromptTemplateConfig
{
    /// <summary>
    /// Semantic Kernel template format.
    /// </summary>
    public const string SemanticKernelTemplateFormat = "semantic-kernel";

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
    /// Format of the prompt template e.g. f-string, semantic-kernel, handlebars, ...
    /// </summary>
    [JsonPropertyName("template_format")]
    [JsonPropertyOrder(1)]
    public string TemplateFormat { get; set; } = SemanticKernelTemplateFormat;

    /// <summary>
    /// Description
    /// </summary>
    [JsonPropertyName("description")]
    [JsonPropertyOrder(2)]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Input configuration (that is, list of all input parameters).
    /// </summary>
    [JsonPropertyName("input")]
    [JsonPropertyOrder(3)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public InputConfig Input { get; set; } = new();

    /// <summary>
    /// Model request settings.
    /// </summary>
    [JsonPropertyName("models")]
    [JsonPropertyOrder(4)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<PromptExecutionSettings> ModelSettings { get; set; } = new();

    /// <summary>
    /// Return the default <see cref="PromptExecutionSettings"/>
    /// </summary>
    public PromptExecutionSettings GetDefaultRequestSettings()
    {
        return this.ModelSettings.FirstOrDefault() ?? new PromptExecutionSettings();
    }

    /// <summary>
    /// Creates a prompt template configuration from JSON.
    /// </summary>
    /// <param name="json">JSON of the prompt template configuration.</param>
    /// <returns>Prompt template configuration.</returns>
    /// <exception cref="ArgumentException">Thrown when the deserialization returns null.</exception>
    public static PromptTemplateConfig FromJson(string json)
    {
        var result = JsonSerializer.Deserialize<PromptTemplateConfig>(json, JsonOptionsCache.ReadPermissive);
        return result ?? throw new ArgumentException("Unable to deserialize prompt template config from argument. The deserialization returned null.", nameof(json));
    }

    internal static PromptTemplateConfig ToPromptTemplateConfig(PromptFunctionModel semanticFunctionConfig)
    {
        return new PromptTemplateConfig()
        {
            TemplateFormat = semanticFunctionConfig.TemplateFormat,
            Description = semanticFunctionConfig.Description,
            Input = new InputConfig()
            {
                Parameters = semanticFunctionConfig.InputParameters.Select(p => new InputParameter()
                {
                    Name = p.Name,
                    Description = p.Description,
                    DefaultValue = p.DefaultValue
                }).ToList()
            },
            ModelSettings = semanticFunctionConfig.ExecutionSettings
        };
    }
}
