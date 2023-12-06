// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Prompt template configuration.
/// </summary>
public sealed class PromptTemplateConfig
{
    /// <summary>
    /// Semantic Kernel template format.
    /// </summary>
    public const string SemanticKernelTemplateFormat = "semantic-kernel";

    /// <summary>
    /// Name of the kernel function.
    /// </summary>
    [JsonPropertyName("name")]
    public string Name { get; set; } = string.Empty;

    /// <summary>
    /// Format of the prompt template e.g. f-string, semantic-kernel, handlebars, ...
    /// </summary>
    [JsonPropertyName("template_format")]
    public string TemplateFormat { get; set; } = SemanticKernelTemplateFormat;

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
    /// Input variables.
    /// </summary>
    [JsonPropertyName("input_variables")]
    public List<InputVariable> InputVariables { get; set; } = new();

    /// <summary>
    /// Output variable.
    /// </summary>
    [JsonPropertyName("output_variable")]
    public OutputVariable? OutputVariable { get; set; }

    /// <summary>
    /// Prompt execution settings.
    /// </summary>
    [JsonPropertyName("execution_settings")]
    public List<PromptExecutionSettings> ExecutionSettings { get; set; } = new();

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptTemplateConfig"/> class.
    /// </summary>
    public PromptTemplateConfig()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptTemplateConfig"/> class.
    /// </summary>
    public PromptTemplateConfig(string template)
    {
        this.Template = template;
    }

    /// <summary>
    /// Return the input variables metadata.
    /// </summary>
    internal List<KernelParameterMetadata> GetKernelParametersMetadata()
    {
        return this.InputVariables.Select(p => new KernelParameterMetadata(p.Name)
        {
            Description = p.Description,
            DefaultValue = p.Default
        }).ToList();
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
}
