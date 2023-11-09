// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Text.Json;
using Markdig.Syntax;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Functions.Markdown.Models;

/*
 
 */
internal class SemanticFunctionModel
{
    public string Type { get; set; } = string.Empty;

    public string? Name { get; set; }

    public string TemplateFormat { get; set; } = string.Empty;

    public string Template { get; set; } = string.Empty;

    public string Description { get; set; } = string.Empty;

    public string? PluginName { get; set; }

    public IList<InputParameterModel> InputParameters { get; set; } = new List<InputParameterModel>();

    public List<AIRequestSettings> ModelSettings { get; set; } = new();

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
            promptTemplateConfig.ModelSettings.Add(modelSettings);
        }
        return promptTemplateConfig;
    }

    public static SemanticFunctionModel FromMarkdown(string text)
    {
        var model = new SemanticFunctionModel();
        var document = Markdig.Markdown.Parse(text);
        var enumerator = document.GetEnumerator();
        while (enumerator.MoveNext())
        {
            if (enumerator.Current is FencedCodeBlock codeBlock)
            {
                if (codeBlock.Info == "sk.prompt")
                {
                    model.Template = codeBlock.Lines.ToString();
                }
                else if (codeBlock.Info == "sk.model_settings")
                {
                    var modelSettings = codeBlock.Lines.ToString();
                    var requestSettings = JsonSerializer.Deserialize<AIRequestSettings>(modelSettings);
                    if (requestSettings is not null)
                    {
                        model.ModelSettings.Add(requestSettings);
                    }
                }
            }
        }

        return model;
    }

    public class InputParameterModel
    {
        public string Name { get; set; } = string.Empty;

        public string Description { get; set; } = string.Empty;

        public string DefaultValue { get; set; } = string.Empty;
    }
}
