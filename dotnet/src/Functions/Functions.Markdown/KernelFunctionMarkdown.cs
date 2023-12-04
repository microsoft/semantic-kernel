// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using System.Text.Json;
using Markdig;
using Markdig.Syntax;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;

namespace Microsoft.SemanticKernel;

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
        Verify.NotNull(resourceName);
        Verify.NotNull(functionName);

        using StreamReader reader = new(Assembly.GetExecutingAssembly().GetManifestResourceStream(resourceName));

        return FromPromptMarkdown(
            reader.ReadToEnd(),
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
        Verify.NotNull(text);
        Verify.NotNull(functionName);

        return KernelFunctionFactory.CreateFromPrompt(
            CreateFromPromptMarkdown(text, functionName),
            promptTemplateFactory,
            loggerFactory);
    }

    #region Private methods
    internal static PromptTemplateConfig CreateFromPromptMarkdown(string text, string functionName)
    {
        PromptTemplateConfig promptFunctionModel = new() { Name = functionName };

        foreach (Block block in Markdown.Parse(text))
        {
            if (block is FencedCodeBlock codeBlock)
            {
                switch (codeBlock.Info)
                {
                    case "sk.prompt":
                        promptFunctionModel.Template = codeBlock.Lines.ToString();
                        break;

                    case "sk.execution_settings":
                        var modelSettings = codeBlock.Lines.ToString();
                        var executionSettings = JsonSerializer.Deserialize<PromptExecutionSettings>(modelSettings);
                        if (executionSettings is not null)
                        {
                            promptFunctionModel.ExecutionSettings.Add(executionSettings);
                        }
                        break;
                }
            }
        }

        return promptFunctionModel;
    }
    #endregion
}
