// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides the configuration information necessary to create a method function configuration template.
/// </summary>
/// <remarks>
/// A method function configuration template is a template that can be used to generate a function to be added to a plugin.
/// Some reasons you would want to do this:
/// 1. It's not possible to modify the existing code to add the KernelFunction attribute.
/// 2. You want to keep the function metadata separate from the function implementation.
/// </remarks>
public sealed class FunctionTemplateConfig
{
    /// <summary>The format of the method function configuration template.</summary>
    private string? _templateFormat;
    /// <summary>The method function configuration template string.</summary>
    private string _template = string.Empty;
    /// <summary>Lazily-initialized input variables.</summary>
    private List<InputVariable>? _inputVariables;

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionTemplateConfig"/> class.
    /// </summary>
    public FunctionTemplateConfig()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="FunctionTemplateConfig"/> class using the specified method function configuration template string.
    /// </summary>
    /// <param name="template">The method function configuration template string that defines the function.</param>
    /// <exception cref="ArgumentNullException"><paramref name="template"/> is null.</exception>
    public FunctionTemplateConfig(string template)
    {
        this.Template = template;
    }

    /// <summary>
    /// Creates a <see cref="FunctionTemplateConfig"/> from the specified JSON.
    /// </summary>
    /// <param name="json">A string containing a JSON representation of the <see cref="FunctionTemplateConfig"/>.</param>
    /// <returns>The deserialized <see cref="FunctionTemplateConfig"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="json"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="json"/> is an invalid JSON representation of a <see cref="FunctionTemplateConfig"/>.</exception>
    public static FunctionTemplateConfig FromJson(string json)
    {
        Verify.NotNullOrWhiteSpace(json);

        Exception? innerException = null;
        FunctionTemplateConfig? config = null;
        try
        {
            config = JsonSerializer.Deserialize<FunctionTemplateConfig>(json, JsonOptionsCache.ReadPermissive);
            if (config is null)
            {
                throw new ArgumentException($"Unable to deserialize {nameof(FunctionTemplateConfig)} from the specified JSON.", nameof(json));
            }

            // Prevent the default value from being any type other than a string.
            // It's a temporary limitation that helps shape the public API surface
            // (changing the type of the Default property to object) now, before the release.
            // This helps avoid a breaking change while a proper solution for
            // dealing with the different deserialization outputs of JSON/YAML method function configuration configurations is being evaluated.
            foreach (var inputVariable in config.InputVariables)
            {
                // The value of the default property becomes a JsonElement after deserialization because that is how the JsonSerializer handles properties of the object type.
                if (inputVariable.Default is JsonElement element)
                {
                    if (element.ValueKind == JsonValueKind.String)
                    {
                        inputVariable.Default = element.ToString();
                    }
                    else
                    {
                        throw new NotSupportedException($"Default value for input variable '{inputVariable.Name}' must be a string. " +
                            $"This is a temporary limitation; future updates are expected to remove this constraint. method function configuration function - '{config.Name ?? config.Description}'.");
                    }
                }
            }
        }
        catch (JsonException e)
        {
            innerException = e;
        }

        return
            config ??
            throw new ArgumentException($"Unable to deserialize {nameof(FunctionTemplateConfig)} from the specified JSON.", nameof(json), innerException);
    }

    /// <summary>
    /// Gets or sets the function name to use by default when creating method function configuration.
    /// </summary>
    /// <remarks>
    /// If the name is null or empty, a random name will be generated dynamically when creating a function.
    /// </remarks>
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    /// <summary>
    /// Gets or sets a function description to use by default when creating method function configuration.
    /// </summary>
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>
    /// Gets the identifier of the Semantic Kernel template format.
    /// </summary>
    public static string SemanticKernelTemplateFormat => "semantic-kernel";

    /// <summary>
    /// Gets or sets the format of the method function configuration template.
    /// </summary>
    /// <remarks>
    /// If no template format is specified, a default format of <see cref="SemanticKernelTemplateFormat"/> is used.
    /// </remarks>
    [JsonPropertyName("template_format")]
    [AllowNull]
    public string TemplateFormat
    {
        get => this._templateFormat ?? SemanticKernelTemplateFormat;
        set => this._templateFormat = value;
    }

    /// <summary>
    /// Gets or sets the method function configuration template string that defines the function.
    /// </summary>
    /// <exception cref="ArgumentNullException"><paramref name="value"/> is null.</exception>
    [JsonPropertyName("template")]
    public string Template
    {
        get => this._template;
        set
        {
            Verify.NotNull(value);
            this._template = value;
        }
    }

    /// <summary>
    /// Gets or sets the collection of input variables used by the method function configuration template.
    /// </summary>
    [JsonPropertyName("input_variables")]
    public List<InputVariable> InputVariables
    {
        get => this._inputVariables ??= [];
        set
        {
            Verify.NotNull(value);
            this._inputVariables = value;
        }
    }

    /// <summary>
    /// Gets or sets the output variable used by the method function configuration template.
    /// </summary>
    [JsonPropertyName("output_variable")]
    public OutputVariable? OutputVariable { get; set; }

    /// <summary>
    /// Converts the <see cref="InputVariable"/> collection into a collection of <see cref="KernelParameterMetadata"/>.
    /// </summary>
    internal IReadOnlyList<KernelParameterMetadata> GetKernelParametersMetadata()
    {
        KernelParameterMetadata[] result = [];
        if (this._inputVariables is List<InputVariable> inputVariables)
        {
            result = new KernelParameterMetadata[inputVariables.Count];
            for (int i = 0; i < result.Length; i++)
            {
                InputVariable p = inputVariables[i];
                result[i] = new KernelParameterMetadata(p.Name)
                {
                    Description = p.Description,
                    DefaultValue = p.Default,
                    IsRequired = p.IsRequired,
                    ParameterType = !string.IsNullOrWhiteSpace(p.JsonSchema) ? null : p.Default?.GetType() ?? typeof(string),
                    Schema = !string.IsNullOrWhiteSpace(p.JsonSchema) ? KernelJsonSchema.Parse(p.JsonSchema!) : null,
                };
            }
        }

        return result;
    }

    /// <summary>
    /// Converts any <see cref="OutputVariable"/> into a <see cref="KernelReturnParameterMetadata"/>.
    /// </summary>
    internal KernelReturnParameterMetadata? GetKernelReturnParameterMetadata() =>
        this.OutputVariable is OutputVariable outputVariable ?
            new KernelReturnParameterMetadata
            {
                Description = outputVariable.Description,
                Schema = KernelJsonSchema.ParseOrNull(outputVariable.JsonSchema)
            } :
            null;
}
