// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel.Functions;

/// <summary>
/// Default implementation of <see cref="IAIServiceConfigurationProvider"/>
/// Uses the service id to select the preferred service provider and then returns the service and associated model settings.
/// </summary>
internal class OrderedIAIServiceConfigurationProvider : IAIServiceConfigurationProvider
{
    /// <inheritdoc/>
    public (T?, AIRequestSettings?) GetAIServiceConfiguration<T>(IAIServiceProvider serviceProvider, List<AIRequestSettings>? modelSettings) where T : IAIService
    {
        if (modelSettings == null || modelSettings.Count == 0)
        {
            var service = serviceProvider.GetService<T>(null);
            if (service != null)
            {
                return (service, modelSettings?.FirstOrDefault<AIRequestSettings>());
            }
        }
        else
        {
            AIRequestSettings? defaultRequestSettings = null;
            foreach (var model in modelSettings)
            {
                if (model.ServiceId is not null)
                {
                    var service = serviceProvider.GetService<T>(model.ServiceId);
                    if (service != null)
                    {
                        return (service, model);
                    }
                }
                else
                {
                    defaultRequestSettings = model;
                }
            }

            if (defaultRequestSettings is not null)
            {
                return (serviceProvider.GetService<T>(null), defaultRequestSettings);
            }
        }

        var names = string.Join("|", modelSettings.Select(model => model.ServiceId).ToArray());
        throw new SKException($"Service of type {typeof(ITextCompletion)} and name {names ?? "<NONE>"} not registered.");
    }
}
