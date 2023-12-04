// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel;

/// <summary>Extension methods for interacting with <see cref="Kernel"/>.</summary>
public static class KernelExtensions
{
    #region CreateFunctionFromMethod
    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via a delegate.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunction CreateFunctionFromMethod(
        this Kernel kernel,
        Delegate method,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);

        return KernelFunctionFactory.CreateFromMethod(method.Method, method.Target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a <see cref="KernelFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="method">The method to be represented via the created <see cref="KernelFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="KernelFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static KernelFunction CreateFunctionFromMethod(
        this Kernel kernel,
        MethodInfo method,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<KernelParameterMetadata>? parameters = null,
        KernelReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);

        return KernelFunctionFactory.CreateFromMethod(method, target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }
    #endregion

    #region CreateFunctionFromPrompt
    // TODO: Revise these CreateFunctionFromPrompt method XML comments

    /// <summary>
    /// Creates a string-to-string prompt function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Plain language definition of the prompt function, using SK template language</param>
    /// <param name="executionSettings">Optional LLM execution settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <param name="promptTemplateFactory">Optional: Prompt template factory</param>
    /// <returns>A function ready to use</returns>
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        string promptTemplate,
        PromptExecutionSettings? executionSettings = null,
        string? functionName = null,
        string? description = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);

        return KernelFunctionFactory.CreateFromPrompt(promptTemplate, executionSettings, functionName, description, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a prompt function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptConfig">Prompt template configuration.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>A function ready to use</returns>
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        PromptTemplateConfig promptConfig,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);

        return KernelFunctionFactory.CreateFromPrompt(promptConfig, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Allow to define a prompt function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Plain language definition of the prompt function, using SK template language</param>
    /// <param name="promptConfig">Prompt template configuration.</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <returns>A function ready to use</returns>
    public static KernelFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        IPromptTemplate promptTemplate,
        PromptTemplateConfig promptConfig,
        string? functionName = null)
    {
        Verify.NotNull(kernel);

        return KernelFunctionFactory.CreateFromPrompt(promptTemplate, promptConfig, kernel.LoggerFactory);
    }
    #endregion

    #region CreatePluginFromObject
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin CreatePluginFromObject<T>(this Kernel kernel, string? pluginName = null)
        where T : new()
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromObject<T>(pluginName, kernel.LoggerFactory);
    }

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin CreatePluginFromObject(this Kernel kernel, object target, string? pluginName = null)
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromObject(target, pluginName, kernel.LoggerFactory);
    }
    #endregion

    #region ImportPluginFromObject
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin ImportPluginFromObject<T>(this Kernel kernel, string? pluginName = null)
        where T : new()
    {
        IKernelPlugin plugin = CreatePluginFromObject<T>(kernel, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and adds it into the plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <param name="serviceProvider">Service provider from which to resolve dependencies, such as <see cref="ILoggerFactory"/>.</param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin AddPluginFromObject<T>(this ICollection<IKernelPlugin> plugins, string? pluginName = null, IServiceProvider? serviceProvider = null)
        where T : new()
    {
        IKernelPlugin plugin = KernelPluginFactory.CreateFromObject<T>(pluginName, serviceProvider?.GetService<ILoggerFactory>());
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin ImportPluginFromObject(this Kernel kernel, object target, string? pluginName = null)
    {
        IKernelPlugin plugin = CreatePluginFromObject(kernel, target, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <param name="serviceProvider">Service provider from which to resolve dependencies, such as <see cref="ILoggerFactory"/>.</param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin AddPluginFromObject(this ICollection<IKernelPlugin> plugins, object target, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        IKernelPlugin plugin = KernelPluginFactory.CreateFromObject(target, pluginName, serviceProvider?.GetService<ILoggerFactory>());
        plugins.Add(plugin);
        return plugin;
    }
    #endregion

    #region CreatePluginFromDirectory
    /// <summary>Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>.</summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/samples/plugins for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>A list of all the prompt functions found in the directory, indexed by plugin name.</returns>
    public static IKernelPlugin CreatePluginFromPromptDirectory(
        this Kernel kernel,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        const string ConfigFile = "config.json";
        const string PromptFile = "skprompt.txt";

        pluginName ??= new DirectoryInfo(pluginDirectory).Name;
        Verify.ValidPluginName(pluginName, kernel.Plugins);
        Verify.DirectoryExists(pluginDirectory);

        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(kernel.LoggerFactory);

        KernelPlugin plugin = new(pluginName);
        ILogger logger = kernel.LoggerFactory.CreateLogger(typeof(Kernel));

        foreach (string functionDirectory in Directory.EnumerateDirectories(pluginDirectory))
        {
            var functionName = Path.GetFileName(functionDirectory);

            // Continue only if prompt template exists
            var promptPath = Path.Combine(functionDirectory, PromptFile);
            if (!File.Exists(promptPath))
            {
                continue;
            }

            // Load prompt configuration. Note: the configuration is optional.
            var configPath = Path.Combine(functionDirectory, ConfigFile);
            var promptConfig = File.Exists(configPath) ?
                PromptTemplateConfig.FromJson(File.ReadAllText(configPath)) :
                new PromptTemplateConfig();
            promptConfig.Name = functionName;

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Config {0}: {1}", functionName, JsonSerializer.Serialize(promptConfig, JsonOptionsCache.WriteIndented));
            }

            // Load prompt template
            promptConfig.Template = File.ReadAllText(promptPath);
            IPromptTemplate promptTemplateInstance = factory.Create(promptConfig);

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Registering function {0}.{1} loaded from {2}", pluginName, functionName, functionDirectory);
            }

            plugin.AddFunction(kernel.CreateFunctionFromPrompt(promptTemplateInstance, promptConfig));
        }

        return plugin;
    }
    #endregion

    #region ImportPluginFromPromptDirectory
    /// <summary>
    /// Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>
    /// and imports it into the <paramref name="kernel"/>'s plugin collection.
    /// </summary>
    /// <remarks>
    /// <para>
    /// A plugin directory contains a set of subdirectories, one for each function in the form of a prompt.
    /// This method accepts the path of the plugin directory. Each subdirectory's name is used as the function name
    /// and may contain only alphanumeric chars and underscores.
    /// </para>
    /// <code>
    /// The following directory structure, with pluginDirectory = "D:\plugins\OfficePlugin",
    /// will create a plugin with three functions:
    /// D:\plugins\
    ///     |__ OfficePlugin\                 # pluginDirectory
    ///         |__ ScheduleMeeting           #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ SummarizeEmailThread      #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    ///         |__ MergeWordAndExcelDocs     #   function directory
    ///             |__ skprompt.txt          #     prompt template
    ///             |__ config.json           #     settings (optional file)
    /// </code>
    /// <para>
    /// See https://github.com/microsoft/semantic-kernel/tree/main/samples/plugins for examples in the Semantic Kernel repository.
    /// </para>
    /// </remarks>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>A list of all the prompt functions found in the directory, indexed by plugin name.</returns>
    public static IKernelPlugin ImportPluginFromPromptDirectory(
        this Kernel kernel,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        IKernelPlugin plugin = CreatePluginFromPromptDirectory(kernel, pluginDirectory, pluginName, promptTemplateFactory);
        kernel.Plugins.Add(plugin);
        return plugin;
    }
    #endregion

    #region InvokePromptAsync
    /// <summary>
    /// Invoke a prompt function using the provided prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Plain language definition of the prompt, using SK prompt template language</param>
    /// <param name="arguments">The operation arguments</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>Function execution result</returns>
    public static Task<FunctionResult> InvokePromptAsync(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            arguments?.ExecutionSettings,
            promptTemplateFactory: promptTemplateFactory);

        return kernel.InvokeAsync(function, arguments);
    }
    #endregion

    #region InvokePromptStreamingAsync
    /// <summary>
    /// Invoke a prompt function using the provided prompt template and stream the results.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the prompt, using SK prompt template language</param>
    /// <param name="arguments">The operation arguments</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Function execution result</returns>
    public static IAsyncEnumerable<StreamingContentBase> InvokePromptStreamingAsync(
        this Kernel kernel,
        string promptTemplate,
        KernelArguments? arguments = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);
        Verify.NotNullOrWhiteSpace(promptTemplate);

        KernelFunction function = KernelFunctionFactory.CreateFromPrompt(
            promptTemplate,
            arguments?.ExecutionSettings,
            promptTemplateFactory: promptTemplateFactory);

        return function.InvokeStreamingAsync<StreamingContentBase>(kernel, arguments, cancellationToken);
    }
    #endregion
}
