// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// <see cref="Kernel"/> extensions methods for Handlebars functionality.
/// </summary>
public static class HandlebarsKernelExtensions
{
    private static readonly HandlebarsPromptTemplateFactory s_promptTemplateFactory = new();

    /// <summary>
    /// Invoke a prompt function using the provided Handlebars prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Plain language definition of the prompt, using Handlebars prompt template language</param>
    /// <param name="executionSettings">Optional LLM execution settings</param>
    /// <returns>Function execution result</returns>
    public static Task<FunctionResult> InvokeHandlebarsPromptAsync(
        this Kernel kernel,
        string promptTemplate,
        PromptExecutionSettings? executionSettings = null) =>
        kernel.InvokeAsync((KernelFunction)KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            executionSettings,
            promptTemplateFactory: s_promptTemplateFactory));
}
