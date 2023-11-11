// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Functions.Markdown.Functions;
using Microsoft.SemanticKernel.Models;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Functions.Markdown.Extensions;

/// <summary>
/// Class for extensions methods to define semantic functions using markdown.
/// </summary>
public static class KernelSemanticFunctionMarkdownExtensions
{
    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="SemanticFunctionConfig"/> to use to create the semantic function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFromMarkdownResource(
        this IKernel kernel,
        string resourceName,
        string? functionName = null,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        functionName ??= Path.GetFileNameWithoutExtension(resourceName);
        return SKFunctionMarkdown.CreateFromResource(resourceName, functionName, pluginName, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="text">YAML representation of the <see cref="SemanticFunctionConfig"/> to use to create the semantic function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory"></param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFromMarkdown(
        this IKernel kernel,
        string text,
        string functionName,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        return SKFunctionMarkdown.CreateFromMarkdown(text, functionName, pluginName, promptTemplateFactory, kernel.LoggerFactory);
    }
}
