// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using System.Text.Json;
using OpenAI.Assistants;

namespace Microsoft.SemanticKernel.Agents.OpenAI.Internal;

#pragma warning disable CS0618 // Type or member is obsolete

/// <summary>
/// Produce the <see cref="AssistantCreationOptions"/> for an assistant according to the requested configuration.
/// </summary>
internal static class AssistantCreationOptionsFactory
{
    public static AssistantCreationOptions CreateAssistantOptions(this PromptTemplateConfig templateConfig, OpenAIAssistantCapabilities capabilities)
    {
        AssistantCreationOptions assistantCreationOptions = capabilities.CreateAssistantCreationOptions(templateConfig.TemplateFormat);

        assistantCreationOptions.Name = templateConfig.Name;
        assistantCreationOptions.Instructions = templateConfig.Template;
        assistantCreationOptions.Description = templateConfig.Description;

        return assistantCreationOptions;
    }

    public static AssistantCreationOptions CreateAssistantOptions(this OpenAIAssistantDefinition definition)
    {
        AssistantCreationOptions assistantCreationOptions = definition.CreateAssistantCreationOptions(PromptTemplateConfig.SemanticKernelTemplateFormat);

        assistantCreationOptions.Name = definition.Name;
        assistantCreationOptions.Instructions = definition.Instructions;
        assistantCreationOptions.Description = definition.Description;

        return assistantCreationOptions;
    }

    private static AssistantCreationOptions CreateAssistantCreationOptions(this OpenAIAssistantCapabilities definition, string templateFormat)
    {
        AssistantCreationOptions assistantCreationOptions =
            new()
            {
                ToolResources =
                    AssistantToolResourcesFactory.GenerateToolResources(
                        definition.EnableFileSearch ? definition.VectorStoreId : null,
                        definition.EnableCodeInterpreter ? definition.CodeInterpreterFileIds : null),
                ResponseFormat = definition.EnableJsonResponse ? AssistantResponseFormat.JsonObject : AssistantResponseFormat.Auto,
                Temperature = definition.Temperature,
                NucleusSamplingFactor = definition.TopP,
            };

        if (definition.Metadata != null)
        {
            foreach (KeyValuePair<string, string> item in definition.Metadata)
            {
                assistantCreationOptions.Metadata[item.Key] = item.Value;
            }
        }

        assistantCreationOptions.Metadata[OpenAIAssistantAgent.TemplateMetadataKey] = templateFormat;

        if (definition.ExecutionOptions != null)
        {
            string optionsJson = JsonSerializer.Serialize(definition.ExecutionOptions);
            assistantCreationOptions.Metadata[OpenAIAssistantAgent.OptionsMetadataKey] = optionsJson;
        }

        if (definition.EnableCodeInterpreter)
        {
            assistantCreationOptions.Tools.Add(ToolDefinition.CreateCodeInterpreter());
        }

        if (definition.EnableFileSearch)
        {
            assistantCreationOptions.Tools.Add(ToolDefinition.CreateFileSearch());
        }

        return assistantCreationOptions;
    }
}
