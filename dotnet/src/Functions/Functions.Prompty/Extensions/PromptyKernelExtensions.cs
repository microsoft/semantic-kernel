// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Microsoft.Extensions.FileProviders;
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
        return kernel.CreateFunctionFromPrompty(promptyTemplate, promptTemplateFactory, promptyFilePath);
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
    /// <param name="promptyFilePath">Optional: File path to the prompty file.</param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptyTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptyTemplate"/> is empty or composed entirely of whitespace.</exception>
    public static KernelFunction CreateFunctionFromPrompty(
        this Kernel kernel,
        string promptyTemplate,
        IPromptTemplateFactory? promptTemplateFactory = null,
        string? promptyFilePath = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptyTemplate);

        var promptTemplateConfig = KernelFunctionPrompty.ToPromptTemplateConfig(promptyTemplate, promptyFilePath);

        return KernelFunctionFactory.CreateFromPrompt(
            promptTemplateConfig,
            promptTemplateFactory ?? KernelFunctionPrompty.s_defaultTemplateFactory,
            kernel.LoggerFactory);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty template file.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptyFilePath">Path to the file containing the Prompty representation of a prompt based <see cref="KernelFunction"/>.</param>
    /// <param name="fileProvider">The representation of the file system to use to retrieve the prompty file. Defaults to <see cref="PhysicalFileProvider"/> scoped to the current directory.</param>
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
        IFileProvider fileProvider,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptyFilePath);
        Verify.NotNull(fileProvider);

        var fileInfo = fileProvider.GetFileInfo(promptyFilePath);
        return CreateFunctionFromPromptyFile(kernel, fileInfo, promptTemplateFactory);
    }

    /// <summary>
    /// Create a <see cref="KernelFunction"/> from a prompty template file.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="fileInfo">The file containing the Prompty representation of a prompt based <see cref="KernelFunction"/>.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a <see cref="AggregatorPromptTemplateFactory"/> will be used with support for Liquid and Handlebars prompt templates.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="fileInfo"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="fileInfo"/> path is not found.</exception>
    public static KernelFunction CreateFunctionFromPromptyFile(
        this Kernel kernel,
        IFileInfo fileInfo,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNull(fileInfo);
        Verify.True(fileInfo.Exists, $"The file '{fileInfo.PhysicalPath}' doesn't exist.");

        using StreamReader reader = new(fileInfo.CreateReadStream());
        var promptyTemplate = reader.ReadToEnd();
        return kernel.CreateFunctionFromPrompty(promptyTemplate, promptTemplateFactory, fileInfo.PhysicalPath);
    }
}
