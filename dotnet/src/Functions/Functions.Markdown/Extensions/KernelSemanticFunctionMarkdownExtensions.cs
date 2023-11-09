// Copyright (c) Microsoft. All rights reserved.

using System.IO;
using System.Reflection;
using Microsoft.SemanticKernel.Functions.Markdown.Models;

namespace Microsoft.SemanticKernel.Functions.Markdown.Extensions;

/// <summary>
/// Class for extensions methods to define semantic functions using markdown.
/// </summary>
public static class KernelSemanticFunctionMarkdownExtensions
{
    /// <summary>
    /// 
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="resourceName"></param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunctionFromMarkdownResource(
        this IKernel kernel,
        string resourceName)
    {
        // Determine path
        var assembly = Assembly.GetExecutingAssembly();
        string resourcePath = resourceName;
        // Format: "{Namespace}.{Folder}.{filename}.{Extension}"
        /*
        if (!name.StartsWith(nameof(SignificantDrawerCompiler)))
        {
            resourcePath = assembly.GetManifestResourceNames()
                .Single(str => str.EndsWith(name));
        }
        */

        using Stream stream = assembly.GetManifestResourceStream(resourcePath);
        using StreamReader reader = new(stream);
        var text = reader.ReadToEnd();

        return kernel.CreateSemanticFunctionFromMarkdown(resourceName, text);
    }

    /// <summary>
    /// 
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="name"></param>
    /// <param name="text"></param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateSemanticFunctionFromMarkdown(
        this IKernel kernel,
        string name,
        string text)
    {
        var model = SemanticFunctionModel.FromMarkdown(text);

        return kernel.CreateSemanticFunction(
           promptTemplate: model.Template,
           promptTemplateConfig: model.GetPromptTemplateConfig(),
           functionName: name);
    }
}
