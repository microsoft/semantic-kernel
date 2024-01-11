// Copyright (c) Microsoft. All rights reserved.

using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.PromptTemplates.Handlebars;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides <see cref="Kernel"/> extensions methods for Handlebars functionality.
/// </summary>
public static class HandlebarsKernelExtensions
{
    private static readonly HandlebarsPromptTemplateFactory s_promptTemplateFactory = new();

    /// <summary>
    /// Invokes a prompt specified via a prompt template in the Handlebars prompt template format.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Prompt template for the function, using Handlebars prompt template language</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The result of the function's execution.</returns>
    public static Task<FunctionResult> InvokeHandlebarsPromptAsync(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default) =>
        kernel.InvokeAsync((KernelFunction)KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            templateFormat: HandlebarsPromptTemplateFactory.HandlebarsTemplateFormat,
            promptTemplateFactory: s_promptTemplateFactory), arguments, cancellationToken);
}
