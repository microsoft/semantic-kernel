// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Models;

/// <summary>
/// Prompt model files.
/// </summary>
public sealed class PromptFunctionModel
{
    /// <summary>
    /// Name of the kernel function.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Format of the prompt template e.g. f-string, semantic-kernel, handlebars, ...
    /// </summary>
    [JsonPropertyName("template_format")]
    public string TemplateFormat { get; set; } = PromptTemplateConfig.SemanticKernelTemplateFormat;

    /// <summary>
    /// The prompt template
    /// </summary>
    [JsonPropertyName("template")]
    public string Template { get; set; } = string.Empty;

    /// <summary>
    /// Description
    /// </summary>
    [JsonPropertyName("description")]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Input parameters.
    /// </summary>
    [JsonPropertyName("input_parameters")]
    public List<InputParameter> InputParameters { get; set; } = new();

    /// <summary>
    /// Model request settings.
    /// </summary>
    [JsonPropertyName("model_settings")]
    public List<AIRequestSettings> ModelSettings { get; set; } = new();

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
        public string Name { get; set; } = string.Empty;

        /// <summary>
        /// Parameter description for UI apps and planner. Localization is not supported here.
        /// </summary>
        [JsonPropertyName("description")]
        public string Description { get; set; } = string.Empty;

        /// <summary>
        /// Default value when nothing is provided.
        /// </summary>
        [JsonPropertyName("default_value")]
        public string DefaultValue { get; set; } = string.Empty;

        /// <summary>
        /// True to indeicate the input parameter is required. True by default.
        /// </summary>
        [JsonPropertyName("is_required")]
        public bool IsRequired { get; set; } = true;
    }
}
