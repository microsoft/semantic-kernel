// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.SemanticFunctions;
using SemanticKernel.Service.CopilotChat.Skills;

namespace SemanticKernel.Service.CopilotChat.Options;

/// <summary>
/// Options for prompts of semantic functions
/// </summary>
public class PluginPromptOptions
{
    /// <summary>
    /// Number of tokens used by the prompt.txt template
    /// </summary>
    public int PromptTokenCount { get; set; }

    /// <summary>
    /// Settings for the text completion request.
    /// </summary>
    public CompleteRequestSettings CompletionSettings { get; set; }

    private readonly ILogger _logger;

    public PluginPromptOptions(int promptTokenCount, CompleteRequestSettings completionSettings, ILogger logger)
    {
        this.PromptTokenCount = promptTokenCount;
        this.CompletionSettings = completionSettings;
        this._logger = logger;
    }

    public PluginPromptOptions(string promptTextPath, string configJsonPath, ILogger logger)
    {
        this._logger = logger;

        if (!File.Exists(promptTextPath))
        {
            var exceptionMsg = $"{Constants.PromptFileName} file does not exist at " + nameof(promptTextPath);
            throw new ArgumentException(exceptionMsg);
        }

        var promptText = File.ReadAllText(promptTextPath);
        this.PromptTokenCount = Utilities.TokenCount(promptText);

        if (File.Exists(configJsonPath))
        {
            try
            {
                var config = PromptTemplateConfig.FromJson(File.ReadAllText(configJsonPath));
                this.CompletionSettings = CompleteRequestSettings.FromCompletionConfig(config.Completion);
            }
            catch (ArgumentException ex)
            {
                const string exceptionAdditionalInfoMsg = "Unable to parse the config file located at " + nameof(ex.ParamName);
                this._logger.LogWarning(exceptionAdditionalInfoMsg);
                throw ex;
            }
        }
        else
        {
            var exceptionMsg = $"{Constants.ConfigFileName} file does not exist at " + nameof(configJsonPath);
            throw new ArgumentException(exceptionMsg);
        }
    }
}
