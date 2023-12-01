// Copyright (c) Microsoft. All rights reserved.
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Services;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Represents a selector which will return a tuple containing instances of <see cref="IAIService"/> and <see cref="PromptExecutionSettings"/> from the specified provider based on the model settings.
/// </summary>
public interface IAIServiceSelector
{
    /// <summary>
    /// Return the AI service and requesting settings from the specified provider based on the model settings.
    /// The returned value is a tuple containing instances of <see cref="IAIService"/> and <see cref="PromptExecutionSettings"/>
    /// </summary>
    /// <typeparam name="T">Type of AI service to return</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">Semantic Kernel callable function interface</param>
    /// <param name="arguments">The function arguments.</param>
    /// <returns></returns>
#pragma warning disable CA1716 // Identifiers should not match keywords
    (T?, PromptExecutionSettings?) SelectAIService<T>(Kernel kernel, KernelFunction function, KernelArguments arguments) where T : class, IAIService;
#pragma warning restore CA1716
}
