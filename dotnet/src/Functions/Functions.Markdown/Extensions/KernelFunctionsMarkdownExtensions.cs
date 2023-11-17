// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Functions.Markdown.Functions;
using Microsoft.SemanticKernel.Models;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Functions.Markdown.Extensions;

/// <summary>
/// Class for extensions methods to define functions using prompt markdown format.
/// </summary>
public static class KernelFunctionsMarkdownExtensions
{
    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="PromptFunctionModel"/> to use to create the semantic function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFunctionFromMarkdownResource(
        this IKernel kernel,
        string resourceName,
        string? functionName = null,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        functionName ??= Path.GetFileNameWithoutExtension(resourceName);
        return SKFunctionMarkdown.FromPromptMarkdownResource(resourceName, functionName, pluginName, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="text">YAML representation of the <see cref="PromptFunctionModel"/> to use to create the semantic function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory"></param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFunctionFromMarkdown(
        this IKernel kernel,
        string text,
        string functionName,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        return SKFunctionMarkdown.FromPromptMarkdown(text, functionName, pluginName, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="PromptFunctionModel"/> to use to create the semantic function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction ImportFunctionFromMarkdownResource(
        this IKernel kernel,
        string resourceName,
        string? functionName = null,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        functionName ??= Path.GetFileNameWithoutExtension(resourceName);
        var skfunction = SKFunctionMarkdown.FromPromptMarkdownResource(resourceName, functionName, pluginName, promptTemplateFactory, kernel.LoggerFactory);
        return kernel.RegisterCustomFunction(skfunction);
    }

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="text">YAML representation of the <see cref="PromptFunctionModel"/> to use to create the semantic function</param>
    /// <param name="functionName">The function name</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory"></param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction ImportFunctionFromMarkdown(
        this IKernel kernel,
        string text,
        string functionName,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var skfunction = SKFunctionMarkdown.FromPromptMarkdown(text, functionName, pluginName, promptTemplateFactory, kernel.LoggerFactory);
        return kernel.RegisterCustomFunction(skfunction);
    }
}
