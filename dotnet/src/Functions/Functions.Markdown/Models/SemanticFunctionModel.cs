// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Functions.Markdown.Models;

/*
 
 */
internal class SemanticFunctionModel
{
    public string Type { get; set; } = string.Empty;

    public string? Name { get; set; }

    public string TemplateFormat { get; set; } = string.Empty;

    public IList<string> Templates { get; set; } = new List<string>();

    public string Description { get; set; } = string.Empty;

    public string? PluginName { get; set; }

    public IList<InputParameterModel> InputParameters { get; set; } = new List<InputParameterModel>();

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

        public string DefaultValue { get; set; } = string.Empty;
    }
}
