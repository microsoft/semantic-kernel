// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.IO;
using System.Linq;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Class for extensions methods to define functions using prompt YAML format.
/// </summary>
public static class PromptYamlKernelExtensions
{
    #region CreateFunctionFromPromptYaml
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a prompt function using the specified YAML.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="text">YAML representation of the <see cref="PromptTemplateConfig"/> to use to create the prompt function</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting the prompt template configuration into a <see cref="IPromptTemplate"/>.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>The created <see cref="KernelFunction"/>.</returns>
    public static KernelFunction CreateFunctionFromPromptYaml(
        this Kernel kernel,
        string text,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        return KernelFunctionYaml.FromPromptYaml(text, promptTemplateFactory, kernel.LoggerFactory);
    }
    #endregion

    #region CreatePluginFromDirectoryYaml
    /// <summary>Creates a plugin containing one function per YAML file in the <paramref name="pluginDirectory"/>.</summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of YAML files, each representing a function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each YAML file's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                      # pluginDirectory
    ///         |__ ScheduleMeeting.yaml           #   YAML function
    ///         |__ SummarizeEmailThread.yaml      #   YAML function
    ///         |__ MergeWordAndExcelDocs.yaml     #   YAML function
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin.</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing prompt functions created from the specified directory.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin CreatePluginFromPromptDirectoryYaml(
        this Kernel kernel,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);

        return CreatePluginFromPromptDirectoryYaml(pluginDirectory, pluginName, promptTemplateFactory, kernel.Services);
    }

    /// <summary>Creates a plugin containing one function per YAML file in the <paramref name="pluginDirectory"/>.</summary>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    private static KernelPlugin CreatePluginFromPromptDirectoryYaml(
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        IServiceProvider? services = null)
    {
        Verify.DirectoryExists(pluginDirectory);
        pluginName ??= new DirectoryInfo(pluginDirectory).Name;

        ILoggerFactory loggerFactory = services?.GetService<ILoggerFactory>() ?? NullLoggerFactory.Instance;

        var functions = new List<KernelFunction>();
        ILogger logger = loggerFactory.CreateLogger(typeof(Kernel)) ?? NullLogger.Instance;

        var functionFiles = Directory.GetFiles(pluginDirectory, "*.yaml").Concat(Directory.GetFiles(pluginDirectory, "*.yml"));

        foreach (string functionFile in functionFiles)
        {
            var functionName = Path.GetFileName(functionFile);
            var functionYaml = File.ReadAllText(functionFile);

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Registering function {0}.{1} loaded from {2}", pluginName, functionName, functionFile);
            }

            functions.Add(KernelFunctionYaml.FromPromptYaml(functionYaml, promptTemplateFactory, loggerFactory));
        }

        return KernelPluginFactory.CreateFromFunctions(pluginName, null, functions);
    }
    #endregion

    #region ImportPlugin/AddFromPromptDirectoryYaml
    /// <summary>Creates a plugin containing one function per YAML file in the <paramref name="pluginDirectory"/>.</summary>
    /// and imports it into the <paramref name="kernel"/>'s plugin collection.
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of YAML files, each representing a function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each YAML file's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                      # pluginDirectory
    ///         |__ ScheduleMeeting.yaml           #   YAML function
    ///         |__ SummarizeEmailThread.yaml      #   YAML function
    ///         |__ MergeWordAndExcelDocs.yaml     #   YAML function
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin.</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing prompt functions created from the specified directory.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static KernelPlugin ImportPluginFromPromptDirectoryYaml(
        this Kernel kernel,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        KernelPlugin plugin = CreatePluginFromPromptDirectoryYaml(kernel, pluginDirectory, pluginName, promptTemplateFactory);
        kernel.Plugins.Add(plugin);
        return plugin;
    }
    #endregion

    /// <summary>Creates a plugin containing one function per YAML file in the <paramref name="pluginDirectory"/>.</summary>
    /// and adds it into the plugin collection.
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of YAML files, each representing a function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each YAML file's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                      # pluginDirectory
    ///         |__ ScheduleMeeting.yaml           #   YAML function
    ///         |__ SummarizeEmailThread.yaml      #   YAML function
    ///         |__ MergeWordAndExcelDocs.yaml     #   YAML function
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/prompt_template_samples for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin.</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">
    /// The <see cref="IPromptTemplateFactory"/> to use when interpreting discovered prompts into <see cref="IPromptTemplate"/>s.
    /// If null, a default factory will be used.
    /// </param>
    /// <returns>A <see cref="KernelPlugin"/> containing prompt functions created from the specified directory.</returns>
    [RequiresUnreferencedCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    [RequiresDynamicCode("Uses reflection to handle various aspects of the function creation and invocation, making it incompatible with AOT scenarios.")]
    public static IKernelBuilderPlugins AddFromPromptDirectoryYaml(
        this IKernelBuilderPlugins plugins,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton<KernelPlugin>(services =>
            CreatePluginFromPromptDirectoryYaml(pluginDirectory, pluginName, promptTemplateFactory, services));

        return plugins;
    }
}
