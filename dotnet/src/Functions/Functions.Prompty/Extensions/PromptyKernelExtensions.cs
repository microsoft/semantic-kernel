// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Microsoft.SemanticKernel.Prompty;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Provides extension methods for creating <see cref="KernelFunction"/>s from the Prompty template format.
/// </summary>
public static class PromptyKernelExtensions
{
    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty template file.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptyFilePath">Path to the file containing the Prompty representation of a prompt based <see cref="KernelFunction"/>.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a <see cref="AggregatorPromptTemplateFactory"/> will be used with support for Liquid and Handlebars prompt templates.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptyFilePath"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptyFilePath"/> is empty or composed entirely of whitespace.</exception>
    public static KernelFunction CreateFunctionFromPromptyFile(
        this Kernel kernel,
        string promptyFilePath,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptyFilePath);

        var promptyTemplate = File.ReadAllText(promptyFilePath);
        return kernel.CreateFunctionFromPrompty(promptyTemplate, promptTemplateFactory);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptyTemplate">Prompty representation of a prompt-based <see cref="KernelFunction"/>.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a <see cref="AggregatorPromptTemplateFactory"/> will be used with support for Liquid and Handlebars prompt templates.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptyTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptyTemplate"/> is empty or composed entirely of whitespace.</exception>
    public static KernelFunction CreateFunctionFromPrompty(
        this Kernel kernel,
        string promptyTemplate,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptyTemplate);

        var promptTemplateConfig = KernelFunctionPrompty.ToPromptTemplateConfig(promptyTemplate);

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplateConfig,
            promptTemplateFactory ?? KernelFunctionPrompty.s_defaultTemplateFactory,
            kernel.LoggerFactory);
    }
}
