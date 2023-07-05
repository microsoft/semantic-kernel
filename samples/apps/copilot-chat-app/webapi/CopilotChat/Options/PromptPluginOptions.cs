// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.SemanticFunctions;
using SemanticKernel.Service.CopilotChat.Skills;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Options for prompts of semantic functions
/// </summary>
public class PromptPluginOptions
{
    /// <summary>
    /// Number of tokens used by the prompt.txt template
    /// </summary>
    public int PromptTokenCount { get; set; }

    /// <summary>
    /// Settings for the text completion request.
    /// </summary>
    public CompleteRequestSettings CompletionSettings { get; set; }

    public PromptPluginOptions(int promptTokenCount, CompleteRequestSettings completionSettings)
    {
        this.PromptTokenCount = promptTokenCount;
        this.CompletionSettings = completionSettings;
    }

    public PromptPluginOptions(string promptTextPath, string configJsonPath)
    {
        if (!File.Exists(promptTextPath))
        {
            var exceptionMsg = "prompt.txt file does not exist at " + promptTextPath;
            throw new ArgumentException(exceptionMsg);
        }

        var promptText = File.ReadAllText(promptTextPath);
        this.PromptTokenCount = Utilities.TokenCount(promptText);

        if (File.Exists(configJsonPath))
        {
            var config = PromptTemplateConfig.FromJson(File.ReadAllText(configJsonPath));
            this.CompletionSettings = CompleteRequestSettings.FromCompletionConfig(config.Completion);
        }
        else
        {
            this.CompletionSettings = new CompleteRequestSettings();
        }
    }
}
