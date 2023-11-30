// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Functions.Yaml.Functions;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the namespace of IKernel
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Class for extensions methods to define functions using prompt YAML format.
/// </summary>
public static class KernelFunctionsPromptYamlExtensions
{
    /// <summary>
    /// Creates an <see cref="KernelFunction"/> instance for a prompt function using the specified YAML resource.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromPromptYamlResource(
        this Kernel kernel,
        string resourceName,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        return KernelFunctionYaml.FromPromptYamlResource(resourceName, promptTemplateFactory, kernel.GetService<ILoggerFactory>());
    }

    /// <summary>
    /// Creates an <see cref="KernelFunction"/> instance for a prompt function using the specified YAML.
    /// </summary>
    /// <param name="kernel">Kernel instance</param>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="pluginName">The optional name of the plug-in associated with this method.</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromPromptYaml(
        this Kernel kernel,
        string text,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        return KernelFunctionYaml.FromPromptYaml(text, promptTemplateFactory, kernel.GetService<ILoggerFactory>());
    }
}
