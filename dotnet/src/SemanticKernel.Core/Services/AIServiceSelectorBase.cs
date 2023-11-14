// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;

namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Base class for implementing <see cref="IAIServiceSelector"/>.
/// </summary>
public abstract class AIServiceSelectorBase : IAIServiceSelector
{
    /// <inheritdoc/>
    public (T?, AIRequestSettings?) SelectAIService<T>(SKContext context, ISKFunction skfunction) where T : IAIService
    {
        var services = context.ServiceProvider.GetServices<T>();
        foreach (var service in services)
        {
            var result = this.SelectAIService<T>(context, skfunction, service);
            if (result is not null)
            {
                return ((T?, AIRequestSettings?))result;
            }
        }

        throw new SKException($"Valid service of type {typeof(T)} not found.");
    }

    /// <summary>
    /// Return the AI service and requesting settings if the specified provider is the valid choice.
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <param name="context"><see cref="SKContext"/></param>
    /// <param name="skfunction"><see cref="ISKFunction"/></param>
    /// <param name="service">Instance of <see cref="IAIService"/></param>
    /// <returns></returns>
    protected abstract (T?, AIRequestSettings?)? SelectAIService<T>(SKContext context, ISKFunction skfunction, T service) where T : IAIService;
}
