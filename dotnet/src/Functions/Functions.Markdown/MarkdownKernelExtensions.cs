// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class for extensions methods to define functions using prompt markdown format.
/// </summary>
public static class MarkdownKernelExtensions
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromMarkdownResource(
        this Kernel kernel,
        string resourceName,
        string? functionName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(resourceName);

        functionName ??= Path.GetFileNameWithoutExtension(resourceName);
        return KernelFunctionMarkdown.FromPromptMarkdownResource(resourceName, functionName, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory"></param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromMarkdown(
        this Kernel kernel,
        string text,
        string functionName,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(text);
        Verify.NotNull(functionName);

        return KernelFunctionMarkdown.FromPromptMarkdown(text, functionName, promptTemplateFactory, kernel.LoggerFactory);
    }
}
