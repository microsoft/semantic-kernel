// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.PromptTemplate.Handlebars;

namespace Microsoft.SemanticKernel;

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
    /// <param name="arguments">The operation arguments</param>
    /// <returns>Function execution result</returns>
    public static Task<FunctionResult> InvokeHandlebarsPromptAsync(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null) =>
        kernel.InvokeAsync((KernelFunction)KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            arguments?.ExecutionSettings,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: s_promptTemplateFactory), arguments);
}
