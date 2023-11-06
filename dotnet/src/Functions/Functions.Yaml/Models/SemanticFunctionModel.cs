// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.TemplateEngine;
using YamlDotNet.Serialization;

namespace Microsoft.SemanticKernel.Functions.Yaml.Models;

/*
    template_format: semantic-kernel
    template:        Say hello world to {{$name}} in {{$language}}
    description:     Say hello to the specified person using the specified language
    plugin_name:     DemoPlugin
    name:            SayHello
    input_parameters:
      - name:          name
        description:   The name of the person to greet
        default_value: John
      - name:          language
        description:   The language to generate the greeting in
        default_value: English
    model_settings:
      - model_id:          gpt-4
        temperature:       1.0
        top_p:             0.0
        presence_penalty:  0.0
        frequency_penalty: 0.0
        max_tokens:        256
        stop_sequences:    []
 */
internal class SemanticFunctionModel
{
    public string Type { get; set; } = string.Empty;

    public string? Name { get; set; }

    [YamlMember(Alias = "template_format", ApplyNamingConventions = false)]
    public string TemplateFormat { get; set; } = string.Empty;

    public string Template { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    [YamlMember(Alias = "plugin_name", ApplyNamingConventions = false)]
    public string? PluginName { get; set; }

    [YamlMember(Alias = "input_parameters", ApplyNamingConventions = false)]
    public IList<InputParameterModel> InputParameters { get; set; } = new List<InputParameterModel>();

    [YamlMember(Alias = "model_settings", ApplyNamingConventions = false)]
    public List<Dictionary<string, object>> ModelSettings { get; set; } = new();

    public PromptTemplateConfig GetPromptTemplateConfig()
    {
        var promptTemplateConfig = new PromptTemplateConfig
        {
            Description = this.Description
        };

        foreach (var inputParameter in this.InputParameters)
        {
            promptTemplateConfig.Input.Parameters.Add(new PromptTemplateConfig.InputParameter
            {
                Name = inputParameter.Name,
                Description = inputParameter.Description,
                DefaultValue = inputParameter.DefaultValue
            });
        }

        foreach (var modelSettings in this.ModelSettings)
        {
            promptTemplateConfig.ModelSettings.Add(new AI.AIRequestSettings
            {
                ServiceId = modelSettings["service_id"]?.ToString(),
                ModelId = modelSettings["model_id"]?.ToString(),
                ExtensionData = modelSettings
            });
        }

        return promptTemplateConfig;
    }

    public class InputParameterModel
    {
        public string Name { get; set; } = string.Empty;

        public string Description { get; set; } = string.Empty;

        [YamlMember(Alias = "default_value", ApplyNamingConventions = false)]
        public string DefaultValue { get; set; } = string.Empty;
    }
}
