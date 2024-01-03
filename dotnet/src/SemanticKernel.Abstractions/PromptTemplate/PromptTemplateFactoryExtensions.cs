// Copyright (c) Microsoft. All rights reserved.

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for operating on <see cref="IPromptTemplateFactory"/> instances.
/// </summary>
public static class PromptTemplateFactoryExtensions
{
    /// <summary>
    /// Creates an instance of <see cref="IPromptTemplate"/> from a <see cref="PromptTemplateConfig"/>.
    /// </summary>
    /// <param name="factory">The factory with which to create the template.</param>
    /// <param name="templateConfig">Prompt template configuration</param>
    /// <returns>The created template.</returns>
    /// <exception cref="KernelException">The factory does not support the specified configuration.</exception>
    public static IPromptTemplate Create(this IPromptTemplateFactory factory, PromptTemplateConfig templateConfig)
    {
        Verify.NotNull(factory);
        Verify.NotNull(templateConfig);

        if (!factory.TryCreate(templateConfig, out IPromptTemplate? result))
        {
            throw new KernelException($"Prompt template format {templateConfig.TemplateFormat} is not supported.");
        }

        return result;
    }
}
