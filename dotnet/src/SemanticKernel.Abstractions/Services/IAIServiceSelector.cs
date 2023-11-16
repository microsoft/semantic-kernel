// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Selector which will return a tuple containing instances of <see cref="IAIService"/> and <see cref="AIRequestSettings"/> from the specified provider based on the model settings.
/// </summary>
public interface IAIServiceSelector
{
    /// <summary>
    /// Return the AI service and requesting settings from the specified provider based on the model settings.
    /// The returned value is a tuple containing instances of <see cref="IAIService"/> and <see cref="AIRequestSettings"/>
    /// </summary>
    /// <typeparam name="T">Type of AI service to return</typeparam>
    /// <param name="context">Semantic Kernel context</param>
    /// <param name="skfunction">Semantic Kernel callable function interface</param>
    /// <returns></returns>
    (T?, AIRequestSettings?) SelectAIService<T>(SKContext context, ISKFunction skfunction) where T : IAIService;
}
