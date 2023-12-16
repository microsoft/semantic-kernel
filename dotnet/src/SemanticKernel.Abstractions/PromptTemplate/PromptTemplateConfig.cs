// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Serialization;
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

    /// <summary>Lazily-initialized input variables.</summary>
    private List<InputVariable>? _inputVariables;

    /// <summary>Lazily-initialized execution settings. The key is the service id or "default" for the default execution settings.</summary>
    private Dictionary<string, PromptExecutionSettings>? _executionSettings;

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
    public List<InputVariable> InputVariables
    {
        get => this._inputVariables ??= new();
        set
        {
            Verify.NotNull(value);
            this._inputVariables = value;
        }
    }

    /// <summary>
    /// Output variable.
    /// </summary>
    [JsonPropertyName("output_variable")]
    public OutputVariable? OutputVariable { get; set; }

    /// <summary>
    /// Prompt execution settings.
    /// </summary>
    [JsonPropertyName("execution_settings")]
    public Dictionary<string, PromptExecutionSettings> ExecutionSettings
    {
        get => this._executionSettings ??= new();
        set
        {
            Verify.NotNull(value);
            this._executionSettings = value;
        }
    }

    /// <summary>
    /// Default execution settings.
    /// </summary>
    public PromptExecutionSettings? DefaultExecutionSettings => this._executionSettings is not null && this._executionSettings.TryGetValue(PromptExecutionSettings.DefaultServiceId, out PromptExecutionSettings? settings) ? settings : null;

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
    /// Adds the <see cref="PromptExecutionSettings"/> to the <see cref="ExecutionSettings"/> dictionary.
    /// </summary>
    /// <remarks>
    /// The key is the service id or "default" for the default execution settings.
    /// </remarks>
    /// <param name="settings">Instance of <see cref="PromptExecutionSettings"/></param>
    /// <param name="serviceId">Service id</param>
    public void AddExecutionSettings(PromptExecutionSettings settings, string? serviceId = null)
    {
        Verify.NotNull(settings);

        var key = serviceId ?? PromptExecutionSettings.DefaultServiceId;
        if (this.ExecutionSettings.ContainsKey(key))
        {
            throw new ArgumentException($"Execution settings for service id '{key}' already exists.");
        }

        this.ExecutionSettings[key] = settings;
    }

    /// <summary>
    /// Return the input variables metadata.
    /// </summary>
    internal IReadOnlyList<KernelParameterMetadata> GetKernelParametersMetadata()
    {
        if (this._inputVariables is List<InputVariable> inputVariables)
        {
            return inputVariables.Select(p => new KernelParameterMetadata(p.Name)
            {
                Description = p.Description,
                DefaultValue = p.Default,
                IsRequired = p.IsRequired,
                ParameterType = !string.IsNullOrWhiteSpace(p.JsonSchema) ? null : typeof(string),
                Schema = !string.IsNullOrWhiteSpace(p.JsonSchema) ? KernelJsonSchema.Parse(p.JsonSchema!) : null,
            }).ToList();
        }

        return Array.Empty<KernelParameterMetadata>();
    }

    /// <summary>
    /// Return the output variable metadata.
    /// </summary>
    internal KernelReturnParameterMetadata? GetKernelReturnParameterMetadata()
    {
        if (this.OutputVariable is not null)
        {
            return new KernelReturnParameterMetadata
            {
                Description = this.OutputVariable.Description,
                Schema = KernelJsonSchema.ParseOrNull(this.OutputVariable.JsonSchema)
            };
        }

        return null;
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
