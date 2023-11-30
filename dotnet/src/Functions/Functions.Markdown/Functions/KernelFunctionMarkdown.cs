// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using System.Text.Json;
using Markdig.Syntax;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel.Functions.Markdown.Functions;

/// <summary>
/// Factory methods for creating <seealso cref="KernelFunction"/> instances.
/// </summary>
public static class KernelFunctionMarkdown
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown resource.
    /// </summary>
    /// <param name="resourceName">Resource containing the markdown representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="functionName">The name of the function.</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction FromPromptMarkdownResource(
        string resourceName,
        string functionName,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        var assembly = Assembly.GetExecutingAssembly();
        string resourcePath = resourceName;

        using Stream stream = assembly.GetManifestResourceStream(resourcePath);
        using StreamReader reader = new(stream);
        var text = reader.ReadToEnd();

        return FromPromptMarkdown(
            text,
            functionName,
            pluginName,
            promptTemplateFactory,
            loggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified markdown text.
    /// </summary>
    /// <param name="text">Markdown representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="functionName">The name of the function.</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this function.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction FromPromptMarkdown(
        string text,
        string functionName,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        return KernelFunctionFactory.CreateFromPrompt(
            CreateFromPromptMarkdown(text, functionName),
            promptTemplateFactory,
            loggerFactory);
    }

    #region Private methods
    internal static PromptTemplateConfig CreateFromPromptMarkdown(string text, string functionName)
    {
        var promptFunctionModel = new PromptTemplateConfig()
        {
            Name = functionName
        };
        var document = Markdig.Markdown.Parse(text);
        var enumerator = document.GetEnumerator();
        while (enumerator.MoveNext())
        {
            if (enumerator.Current is FencedCodeBlock codeBlock)
            {
                if (codeBlock.Info == "sk.prompt")
                {
                    promptFunctionModel.Template = codeBlock.Lines.ToString();
                }
                else if (codeBlock.Info == "sk.execution_settings")
                {
                    var modelSettings = codeBlock.Lines.ToString();
                    var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(modelSettings);
                    if (executionSettings is not null)
                    {
                        promptFunctionModel.ExecutionSettings.Add(executionSettings);
                    }
                }
            }
        }

        return promptFunctionModel;
    }
    #endregion
}
