// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.TemplateEngine.Basic;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods to define semantic functions using the basic prompt template factory.
/// </summary>
public static class KernelBasicPromptTemplateExtensions
{
    /// <summary>
    /// Build and register a function in the internal function collection, in a global generic plugin.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="templateString">Prompt template string.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    public static ISKFunction RegisterSemanticFunction(
        this IKernel kernel,
        string functionName,
        string templateString,
        PromptTemplateConfig promptTemplateConfig)
    {
        var promptTemplateFactory = new BasicPromptTemplateFactory(loggerFactory: kernel.LoggerFactory);
        var promptTemplate = promptTemplateFactory.Create(templateString, promptTemplateConfig);
        return kernel.RegisterSemanticFunction(functionName, promptTemplateConfig, promptTemplate);
    }

    /// <summary>
    /// Build and register a function in the internal function collection, in a global generic plugin.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="pluginName"></param>
    /// <param name="functionName">Name of the semantic function. The name can contain only alphanumeric chars + underscore.</param>
    /// <param name="templateString">Prompt template string.</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <returns>A C# function wrapping AI logic, usually defined with natural language</returns>
    public static ISKFunction RegisterSemanticFunction(
        this IKernel kernel,
        string pluginName,
        string functionName,
        string templateString,
        PromptTemplateConfig promptTemplateConfig)
    {
        var promptTemplateFactory = new BasicPromptTemplateFactory(loggerFactory: kernel.LoggerFactory);
        var promptTemplate = promptTemplateFactory.Create(templateString, promptTemplateConfig);
        return kernel.RegisterSemanticFunction(pluginName, functionName, promptTemplateConfig, promptTemplate);
    }
}
