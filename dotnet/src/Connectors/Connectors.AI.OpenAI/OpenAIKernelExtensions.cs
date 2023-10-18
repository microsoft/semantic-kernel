// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.AI.OpenAI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extension methods for <see cref="IKernel"/> using OpenAI request settings.
/// </summary>
public static class OpenAIKernelExtensions
{
    /// <summary>
    /// Define a string-to-string semantic function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="requestSettings">OpenAI LLM request settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="pluginName">Optional plugin name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunction(
        this IKernel kernel,
        string promptTemplate,
        OpenAIRequestSettings requestSettings,
        string? functionName = null,
        string? pluginName = null,
        string? description = null)
    {
        return kernel.CreateSemanticFunction(
            promptTemplate,
            functionName,
            pluginName,
            description,
            requestSettings);
    }

    /// <summary>
    /// Invoke a semantic function using the provided prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="requestSettings">OpenAI LLM request settings</param>
    /// <param name="functionName">Options name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="pluginName">Optional plugin name, for namespacing and avoid collisions</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <returns>A function ready to use</returns>
    public static Task<KernelResult> InvokeSemanticFunctionAsync(
        this IKernel kernel,
        string promptTemplate,
        OpenAIRequestSettings requestSettings,
        string? functionName = null,
        string? pluginName = null,
        string? description = null)
    {
        return kernel.InvokeSemanticFunctionAsync(
            promptTemplate,
            functionName,
            pluginName,
            description,
            requestSettings);
    }
}
