// Copyright (c) Microsoft. All rights reserved.
using System.Collections.Generic;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Services;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Factory which will return an <see cref="IAIService"/> instance from the specified provider based on the model settings.
/// </summary>
public interface IAIServiceConfigurationProvider
{
    /// <summary>
    /// Return the AI service configuration from the specified provider based on the model settings.
    /// The AI service configuration is a tuple containing instances of <see cref="IAIService"/> and <see cref="AIRequestSettings"/>
    /// </summary>
    /// <typeparam name="T"></typeparam>
    /// <param name="serviceProvider">AI service provider</param>
    /// <param name="modelSettings">Collection of model settings</param>
    /// <returns></returns>
    (T?, AIRequestSettings?) GetAIServiceConfiguration<T>(IAIServiceProvider serviceProvider, List<AIRequestSettings>? modelSettings) where T : IAIService;
}
