// Copyright (c) Microsoft. All rights reserved.

<<<<<<< Updated upstream
<<<<<<< Updated upstream
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
=======
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.TemplateEngine;

#pragma warning disable IDE0130
>>>>>>> origin/main
namespace Microsoft.SemanticKernel.Experimental.Orchestration;
#pragma warning restore IDE0130
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes

/// <summary>
/// Extension methods for PromptTemplateConfig
/// </summary>
internal static class PromptTemplateConfigExtensions
{
    /// <summary>
    /// Set the max_tokens request setting to be used by OpenAI models
    /// </summary>
    /// <param name="config">PromptTemplateConfig instance</param>
    /// <param name="maxTokens">Value of max tokens to set</param>
    internal static void SetMaxTokens(this PromptTemplateConfig config, int maxTokens)
    {
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
<<<<<<< main
        var executionSettings = config.ExecutionSettings;
        foreach (var setting in executionSettings)
        {
            if (setting.Value.ExtensionData is not null)
            {
                setting.Value.ExtensionData["max_tokens"] = maxTokens;
            }
        }
=======
<<<<<<< HEAD
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        var executionSettings = config.ExecutionSettings;
        foreach (var setting in executionSettings)
        {
            if (setting.Value.ExtensionData is not null)
            {
                setting.Value.ExtensionData["max_tokens"] = maxTokens;
            }
        }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
        AIRequestSettings requestSettings = config.GetDefaultRequestSettings() ?? new();
        if (config.ModelSettings.Count == 0)
        {
            config.ModelSettings.Add(requestSettings);
        }
        requestSettings.ExtensionData["max_tokens"] = maxTokens;
>>>>>>> 9cfcc609b1cbe6e1d6975df1d665fa0b064c5624
>>>>>>> origin/main
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    }
}
