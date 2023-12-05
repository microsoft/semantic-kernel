// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class for extensions methods to define functions using prompt YAML format.
/// </summary>
public static class PromptYamlKernelExtensions
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified YAML resource.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="resourceName">Resource containing the YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromPromptYamlResource(
        this Kernel kernel,
        string resourceName,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        return KernelFunctionYaml.FromPromptYamlResource(resourceName, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified YAML.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">>Prompt template factory.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromPromptYaml(
        this Kernel kernel,
        string text,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        return KernelFunctionYaml.FromPromptYaml(text, promptTemplateFactory, kernel.LoggerFactory);
    }
}
