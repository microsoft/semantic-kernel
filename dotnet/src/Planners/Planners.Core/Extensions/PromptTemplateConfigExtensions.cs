// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
using System.Linq;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.SemanticFunctions;
#pragma warning restore IDE0130

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
        config.Models ??= new();

        if (config.Models.Count == 0)
        {
            config.Models.Add(new AIRequestSettings());
        }
        config.Models.First<AIRequestSettings>().ExtensionData["max_tokens"] = maxTokens;
    }
}
