// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel.SemanticFunctions;

/// <summary>
/// Prompt configuration.
/// </summary>
public class PromptConfig
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
    /// Settings for a prompt request. This supports text completions, image generation, etc.
    /// </summary>
    public class PromptRequestSettings
    {
        /// <summary>
        /// Order for this model.
        /// </summary>
        public int? order { get; set; }

        /// <summary>
        /// Identifier for an AI model.
        /// </summary>
        public string? ModelId { get; set; }

        /// <summary>
        /// Identifier for a AI service provider. This is deployment agnostic.
        /// </summary>
        public string? ProviderId { get; set; }

        /// <summary>
        /// Request properties.
        /// </summary>
        public JsonObject Properties { get; set; } = new();
    }

    /// <summary>
    /// Prompt version
    /// </summary>
    [JsonPropertyName("promptVersion")]
    [JsonPropertyOrder(1)]
    public int PromptVersion { get; set; } = 1;

    /// <summary>
    /// Template type
    /// </summary>
    [JsonPropertyName("templateType")]
    [JsonPropertyOrder(2)]
    public string TemplateType { get; set; } = "semantic-kernel";

    /// <summary>
    /// Template
    /// </summary>
    [JsonPropertyName("template")]
    [JsonPropertyOrder(3)]
    public string? Template { get; set; }

    /// <summary>
    /// Template path
    /// </summary>
    [JsonPropertyName("templatePath")]
    [JsonPropertyOrder(4)]
    public string? TemplatePath { get; set; }

    /// <summary>
    /// Plugin name
    /// </summary>
    [JsonPropertyName("pluginName")]
    [JsonPropertyOrder(5)]
    public string? PluginName
    {
        get
        {
            return this._pluginName;
        }
        set
        {
            Verify.ValidPluginName(value);
            this._pluginName = value;
        }
    }

    /// <summary>
    /// Function name
    /// </summary>
    [JsonPropertyName("functionName")]
    [JsonPropertyOrder(6)]
    public string? FunctionName
    {
        get
        {
            return this._functionName;
        }
        set
        {
            Verify.ValidFunctionName(value);
            this._functionName = value;
        }
    }

    /// <summary>
    /// Description
    /// </summary>
    [JsonPropertyName("description")]
    [JsonPropertyOrder(7)]
    public string Description { get; set; } = string.Empty;

    /// <summary>
    /// Input parameters
    /// </summary>
    [JsonPropertyName("inputParameters")]
    [JsonPropertyOrder(8)]
    [JsonIgnore(Condition = JsonIgnoreCondition.WhenWritingNull)]
    public List<InputParameter> InputParameters { get; set; } = new();

    /// <summary>
    /// List of PromptRequestSettings
    /// </summary>
    [JsonPropertyName("requestSettings")]
    [JsonPropertyOrder(9)]
    public List<PromptRequestSettings>? RequestSettings { get; set; }

    #region internal

    /// <summary>
    /// Return the list of parameters used by the function as a list of ParameterView instances.
    /// </summary>
    /// <returns>List of parameters</returns>
    internal IList<ParameterView> GetParameters()
    {
        List<ParameterView> parameters = new();
        foreach (var p in this.InputParameters)
        {
            parameters.Add(new ParameterView(p.Name, p.Description, p.DefaultValue));
        }
        return parameters;
    }

    /// <summary>
    /// Render the template using the information in the context
    /// </summary>
    /// <param name="engine">Prompt template engine</param>
    /// <param name="executionContext">Kernel execution context helpers</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Prompt rendered to string</returns>
    internal Task<string> RenderAsync(IPromptTemplateEngine engine, SKContext executionContext, CancellationToken cancellationToken = default)
    {
        return engine.RenderAsync(this.GetTemplate(), executionContext, cancellationToken);
    }

    /// <summary>
    /// Get the prompt template.
    /// </summary>
    /// <returns>Prompt template</returns>
    internal string GetTemplate()
    {
        if (this.Template is null)
        {
            throw new KernelException(
                KernelException.ErrorCodes.InvalidTemplate,
                "A template cannot be null.");
        }

        // TODO Add support for loading from the template path

        return this.Template;
    }

    /// <summary>
    /// Get the default request settings to be used when the associated prompt is executed.
    /// </summary>
    /// <returns>JSON string containing the default request settings</returns>
    internal string? GetDefaultRequestSettingsAsJson()
    {
        if (this.RequestSettings is not null && this.RequestSettings.Count > 0)
        {
            // Initial implementation only supports a single instance of request settings
            // and the first item in the list will be the default settings.
            // Later this pattern will be extended to allow the request settings to be selected
            // when the semantic function is invoked.
            var defaultSettings = this.RequestSettings[0];
            return defaultSettings.Properties.ToJson();
        }

        return null;
    }

    #endregion

    #region private

    private string? _functionName;
    private string? _pluginName;

    #endregion
}
