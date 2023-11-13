// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using System.Text.Json;
using Markdig.Syntax;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Models;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel.Functions.Markdown.Functions;

/// <summary>
/// Factory methods for creating <seealso cref="ISKFunction"/> instances.
/// </summary>
public static class SKFunctionMarkdown
{
    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="resourceName">Resource containing the markdown representation of the <see cref="PromptModel"/> to use to create the semantic function</param>
    /// <param name="functionName">The name of the function.</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFromResource(
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

        return CreateFromMarkdown(
            text,
            functionName,
            pluginName,
            promptTemplateFactory,
            loggerFactory);
    }

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a semantic function using the specified markdown text.
    /// </summary>
    /// <param name="text">Markdown representation of the <see cref="PromptModel"/> to use to create the semantic function</param>
    /// <param name="functionName">The name of the function.</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this function.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>The created <see cref="ISKFunction"/>.</returns>
    public static ISKFunction CreateFromMarkdown(
        string text,
        string functionName,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        ILoggerFactory? loggerFactory = null)
    {
        return SKFunction.Create(
            CreateSemanticFunctionConfigFromMarkdown(text, functionName),
            pluginName,
            promptTemplateFactory,
            loggerFactory);
    }

    #region Private methods
    internal static PromptModel CreateSemanticFunctionConfigFromMarkdown(string text, string functionName)
    {
        var config = new PromptModel()
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
                    config.Template = codeBlock.Lines.ToString();
                }
                else if (codeBlock.Info == "sk.model_settings")
                {
                    var modelSettings = codeBlock.Lines.ToString();
                    var requestSettings = JsonSerializer.Deserialize<AIRequestSettings>(modelSettings);
                    if (requestSettings is not null)
                    {
                        config.ModelSettings.Add(requestSettings);
                    }
                }
            }
        }

        return config;
    }
    #endregion
}
