// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Base classe for implementing <see cref="IAIServiceSelector"/>.
/// </summary>
public abstract class AIServiceSelectorBase : IAIServiceSelector
{
    /// <inheritdoc/>
    public (T?, AIRequestSettings?) SelectAIService<T>(string renderedPrompt, IAIServiceProvider serviceProvider, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService
    {
        var services = serviceProvider.GetServices<T>();
        foreach (var service in services)
        {
            var result = this.SelectAIService<T>(renderedPrompt, service, modelSettings);
            if (result is not null)
            {
                return ((T?, AIRequestSettings?))result;
            }
        }

        throw new SKException($"Valid service of type {typeof(T)} not found.");
    }

    /// <summary>
    /// Return the AI service and requesting settings if the specified provider is the vaid choice.
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <param name="renderedPrompt"></param>
    /// <param name="service"></param>
    /// <param name="modelSettings"></param>
    /// <returns></returns>
    protected abstract (T?, AIRequestSettings?)? SelectAIService<T>(string renderedPrompt, T service, IReadOnlyList<AIRequestSettings>? modelSettings) where T : IAIService;
}
