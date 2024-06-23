// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class for extensions methods to define functions using method YAML format.
/// </summary>
public static class MethodYamlKernelExtensions
{
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method function using the specified YAML.
    /// Some reasons you would want to do this:
    /// 1. It's not possible to modify the existing code to add the KernelFunction attribute.
    /// 2. You want to keep the function metadata separate from the function implementation.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="text">YAML representation of the <see cref="MethodTemplateConfig"/> to use to create the yaml method function</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromMethodYaml(
        this Kernel kernel,
        object plugin,
        string text)
    {
        //TODO: Understand how to create and return kernel function without a prompt
        return KernelFunctionYaml.FromMethodYaml(text, plugin, kernel.LoggerFactory);
    }
}
