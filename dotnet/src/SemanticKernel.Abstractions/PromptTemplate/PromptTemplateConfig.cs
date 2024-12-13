// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Text.Json.Serialization.Metadata;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides the configuration information necessary to create a prompt template.
/// </summary>
/// <remarks>
/// A prompt template is a template that can be used to generate a prompt to be submitted to an AI service.
/// For basic prompts, the template may be supplied as a simple string. For more complex prompts, more information
/// is desirable for describing the prompt template, such as details on input variables expected by the template.
/// This can all be provided by a <see cref="PromptTemplateConfig"/>, where its <see cref="PromptTemplateConfig.Template"/>
/// is the prompt template string itself, then with other properties set with additional information. To create the
/// actual prompt template, a <see cref="IPromptTemplateFactory"/> is used to create an <see cref="IPromptTemplate"/>;
/// this is done automatically by the APIs that accept a <see cref="PromptTemplateConfig"/>, using a default template
/// factory that understands the <see cref="PromptTemplateConfig.SemanticKernelTemplateFormat"/> format, but with the
/// ability to supply other factories for interpreting other formats.
/// </remarks>
public sealed class PromptTemplateConfig
{
    /// <summary>The format of the prompt template.</summary>
    private string? _templateFormat;
    /// <summary>The prompt template string.</summary>
    private string _template = string.Empty;
    /// <summary>Lazily-initialized input variables.</summary>
    private List<InputVariable>? _inputVariables;
    /// <summary>Lazily-initialized execution settings. The key is the service ID, or <see cref="PromptExecutionSettings.DefaultServiceId"/> for the default execution settings.</summary>
    private Dictionary<string, PromptExecutionSettings>? _executionSettings;

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptTemplateConfig"/> class.
    /// </summary>
    public PromptTemplateConfig()
    {
    }

    /// <summary>
    /// Initializes a new instance of the <see cref="PromptTemplateConfig"/> class using the specified prompt template string.
    /// </summary>
    /// <param name="template">The prompt template string that defines the prompt.</param>
    /// <exception cref="ArgumentNullException"><paramref name="template"/> is null.</exception>
    public PromptTemplateConfig(string template)
    {
        this.Template = template;
    }

    /// <summary>
    /// Creates a <see cref="PromptTemplateConfig"/> from the specified JSON.
    /// </summary>
    /// <param name="json">A string containing a JSON representation of the <see cref="PromptTemplateConfig"/>.</param>
    /// <returns>The deserialized <see cref="PromptTemplateConfig"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="json"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="json"/> is an invalid JSON representation of a <see cref="PromptTemplateConfig"/>.</exception>
    [RequiresUnreferencedCode("Uses reflection to deserialize the prompt template config from JSON, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to deserialize the prompt template config from JSON, making it incompatible with AOT scenarios.")]
    public static PromptTemplateConfig FromJson(string json)
    {
        return FromJsonInternal(json, jsonSerializerOptions: null);
    }

    /// <summary>
    /// Creates a <see cref="PromptTemplateConfig"/> from the specified JSON.
    /// </summary>
    /// <param name="json">A string containing a JSON representation of the <see cref="PromptTemplateConfig"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to deserialize the prompt template config from JSON.</param>
    /// <returns>The deserialized <see cref="PromptTemplateConfig"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="json"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="json"/> is an invalid JSON representation of a <see cref="PromptTemplateConfig"/>.</exception>
    [UnconditionalSuppressMessage("Trimming", "IL2026:Members annotated with 'RequiresUnreferencedCodeAttribute' require dynamic access otherwise can break functionality when trimming application code", Justification = "This method is AOT safe.")]
    [UnconditionalSuppressMessage("AOT", "IL3050:Calling members annotated with 'RequiresDynamicCodeAttribute' may break functionality when AOT compiling.", Justification = "This method is AOT safe.")]
    [Experimental("SKEXP0120")]
    public static PromptTemplateConfig FromJson(string json, JsonSerializerOptions jsonSerializerOptions)
    {
        return FromJsonInternal(json, jsonSerializerOptions);
    }

    /// <summary>
    /// Gets or sets the function name to use by default when creating prompt functions using this configuration.
    /// </summary>
    /// <remarks>
    /// If the name is null or empty, a random name will be generated dynamically when creating a function.
    /// </remarks>
    [JsonPropertyName("name")]
    public string? Name { get; set; }

    /// <summary>
    /// Gets or sets a function description to use by default when creating prompt functions using this configuration.
    /// </summary>
    [JsonPropertyName("description")]
    public string? Description { get; set; }

    /// <summary>
    /// Gets the identifier of the Semantic Kernel template format.
    /// </summary>
    public static string SemanticKernelTemplateFormat => "semantic-kernel";

    /// <summary>
    /// Gets or sets the format of the prompt template.
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
    /// Gets or sets the prompt template string that defines the prompt.
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
    /// Gets or sets the collection of input variables used by the prompt template.
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
    /// Gets or sets the output variable used by the prompt template.
    /// </summary>
    [JsonPropertyName("output_variable")]
    public OutputVariable? OutputVariable { get; set; }

    /// <summary>
    /// Gets or sets the collection of execution settings used by the prompt template.
    /// </summary>
    /// <remarks>
    /// The settings dictionary is keyed by the service ID, or <see cref="PromptExecutionSettings.DefaultServiceId"/> for the default execution settings.
    /// When setting, the service id of each <see cref="PromptExecutionSettings"/> must match the key in the dictionary.
    /// </remarks>
    [JsonPropertyName("execution_settings")]
    public Dictionary<string, PromptExecutionSettings> ExecutionSettings
    {
        get => this._executionSettings ??= [];
        set
        {
            Verify.NotNull(value);

            if (value.Count != 0)
            {
                foreach (var kv in value)
                {
                    // Ensures that if a service id is provided it must match the key in the dictionary.
                    if (!string.IsNullOrWhiteSpace(kv.Value.ServiceId) && kv.Key != kv.Value.ServiceId)
                    {
                        throw new ArgumentException($"Service id '{kv.Value.ServiceId}' must match the key '{kv.Key}'.", nameof(this.ExecutionSettings));
                    }
                }
            }

            this._executionSettings = value;
        }
    }

    /// <summary>
    /// Gets or sets a value indicating whether to allow potentially dangerous content to be inserted into the prompt from functions.
    /// </summary>
    /// <remarks>
    /// The default is false.
    /// When set to true the return values from functions only are treated as safe content.
    /// For prompts which are being used with a chat completion service this should be set to false to protect against prompt injection attacks.
    /// When using other AI services e.g. Text-To-Image this can be set to true to allow for more complex prompts.
    /// </remarks>
    [JsonPropertyName("allow_dangerously_set_content")]
    public bool AllowDangerouslySetContent { get; set; } = false;

    /// <summary>
    /// Gets the default execution settings from <see cref="ExecutionSettings"/>.
    /// </summary>
    /// <remarks>
    /// If no default is specified, this will return null.
    /// </remarks>
    public PromptExecutionSettings? DefaultExecutionSettings => this._executionSettings?.TryGetValue(PromptExecutionSettings.DefaultServiceId, out PromptExecutionSettings? settings) is true ? settings : null;

    /// <summary>
    /// Adds the specified <see cref="PromptExecutionSettings"/> to the <see cref="ExecutionSettings"/> dictionary.
    /// </summary>
    /// <remarks>
    /// The key is the service ID, or <see cref="PromptExecutionSettings.DefaultServiceId"/> for the default execution settings.
    /// If the service ID is null, <see cref="PromptExecutionSettings.DefaultServiceId"/> will be used.
    /// </remarks>
    /// <param name="settings">The <see cref="PromptExecutionSettings"/> to add to the dictionary.</param>
    /// <param name="serviceId">The service ID with which to associated <paramref name="settings"/>, or null if this should be the default settings.</param>
    public void AddExecutionSettings(PromptExecutionSettings settings, string? serviceId = null)
    {
        Verify.NotNull(settings);

        if (!string.IsNullOrWhiteSpace(serviceId) && !string.IsNullOrWhiteSpace(settings.ServiceId))
        {
            throw new ArgumentException($"Service id must not be passed when '{nameof(settings.ServiceId)}' is already provided in execution settings.", nameof(serviceId));
        }

        var key = serviceId ?? settings.ServiceId ?? PromptExecutionSettings.DefaultServiceId;

        if (this.ExecutionSettings.ContainsKey(key))
        {
            throw new ArgumentException($"Execution settings for service id '{key}' already exists.", nameof(serviceId));
        }

        this.ExecutionSettings[key] = settings;
    }

    /// <summary>
    /// Converts the <see cref="InputVariable"/> collection into a collection of <see cref="KernelParameterMetadata"/>.
    /// </summary>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> for schema generation.</param>
    internal IReadOnlyList<KernelParameterMetadata> GetKernelParametersMetadata(JsonSerializerOptions jsonSerializerOptions)
    {
        KernelParameterMetadata[] result = [];
        if (this._inputVariables is List<InputVariable> inputVariables)
        {
            result = new KernelParameterMetadata[inputVariables.Count];
            for (int i = 0; i < result.Length; i++)
            {
                InputVariable p = inputVariables[i];
                result[i] = new KernelParameterMetadata(p.Name, jsonSerializerOptions)
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
    /// Converts the <see cref="InputVariable"/> collection into a collection of <see cref="KernelParameterMetadata"/>.
    /// </summary>
    [RequiresUnreferencedCode("Uses reflection to generate JSON schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to generate JSON schema, making it incompatible with AOT scenarios.")]
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
    [RequiresUnreferencedCode("Uses reflection to generate JSON schema, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to generate JSON schema, making it incompatible with AOT scenarios.")]
    internal KernelReturnParameterMetadata? GetKernelReturnParameterMetadata() =>
        this.OutputVariable is OutputVariable outputVariable ?
            new KernelReturnParameterMetadata
            {
                Description = outputVariable.Description,
                Schema = KernelJsonSchema.ParseOrNull(outputVariable.JsonSchema)
            } :
            null;

    /// <summary>
    /// Converts any <see cref="OutputVariable"/> into a <see cref="KernelReturnParameterMetadata"/>.
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to generate and parse JSON schema.</param>"
    /// </summary>
    internal KernelReturnParameterMetadata? GetKernelReturnParameterMetadata(JsonSerializerOptions jsonSerializerOptions) =>
        this.OutputVariable is OutputVariable outputVariable ?
            new KernelReturnParameterMetadata(jsonSerializerOptions)
            {
                Description = outputVariable.Description,
                Schema = KernelJsonSchema.ParseOrNull(outputVariable.JsonSchema)
            } :
            null;

    /// <summary>
    /// Creates a <see cref="PromptTemplateConfig"/> from the specified JSON.
    /// </summary>
    /// <param name="json">A string containing a JSON representation of the <see cref="PromptTemplateConfig"/>.</param>
    /// <param name="jsonSerializerOptions">The <see cref="JsonSerializerOptions"/> to deserialize the prompt template config from JSON.</param>
    /// <returns>The deserialized <see cref="PromptTemplateConfig"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="json"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="json"/> is an invalid JSON representation of a <see cref="PromptTemplateConfig"/>.</exception>
    [RequiresUnreferencedCode("Uses reflection for deserialization if no JSOs are provided, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection for deserialization if no JSOs are provided, making it incompatible with AOT scenarios.")]
    private static PromptTemplateConfig FromJsonInternal(string json, JsonSerializerOptions? jsonSerializerOptions)
    {
        Verify.NotNullOrWhiteSpace(json);

        Exception? innerException = null;
        PromptTemplateConfig? config = null;
        try
        {
            if (jsonSerializerOptions is not null)
            {
                JsonTypeInfo<PromptTemplateConfig> typeInfo = (JsonTypeInfo<PromptTemplateConfig>)jsonSerializerOptions.GetTypeInfo(typeof(PromptTemplateConfig));
                config = JsonSerializer.Deserialize<PromptTemplateConfig>(json, typeInfo);
            }
            else
            {
                config = JsonSerializer.Deserialize<PromptTemplateConfig>(json);
            }

            if (config is null)
            {
                throw new ArgumentException($"Unable to deserialize {nameof(PromptTemplateConfig)} from the specified JSON.", nameof(json));
            }

            // Prevent the default value from being any type other than a string.
            // It's a temporary limitation that helps shape the public API surface
            // (changing the type of the Default property to object) now, before the release.
            // This helps avoid a breaking change while a proper solution for
            // dealing with the different deserialization outputs of JSON/YAML prompt configurations is being evaluated.
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
                            $"This is a temporary limitation; future updates are expected to remove this constraint. Prompt function - '{config.Name ?? config.Description}'.");
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
            throw new ArgumentException($"Unable to deserialize {nameof(PromptTemplateConfig)} from the specified JSON.", nameof(json), innerException);
    }
}
