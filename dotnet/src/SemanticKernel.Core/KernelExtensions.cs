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
using Microsoft.Extensions.Logging.Abstractions;
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

    #region CreatePluginFromType
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin CreatePluginFromType<T>(this Kernel kernel, string? pluginName = null)
    {
        Verify.NotNull(kernel);

        return KernelPluginFactory.CreateFromType<T>(pluginName, kernel.Services);
    }
    #endregion

    #region CreatePluginFromObject
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

    #region ImportPlugin/AddFromType
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelPlugin ImportPluginFromType<T>(this Kernel kernel, string? pluginName = null)
    {
        IKernelPlugin plugin = CreatePluginFromType<T>(kernel, pluginName);
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
    public static IKernelPlugin AddFromType<T>(this ICollection<IKernelPlugin> plugins, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        Verify.NotNull(plugins);

        IKernelPlugin plugin = KernelPluginFactory.CreateFromType<T>(pluginName, serviceProvider);
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and adds it into the plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelBuilderPlugins AddFromType<T>(this IKernelBuilderPlugins plugins, string? pluginName = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton<IKernelPlugin>(serviceProvider => KernelPluginFactory.CreateFromType<T>(pluginName, serviceProvider));

        return plugins;
    }

    /// <summary>Adds the <paramref name="plugin"/> to the <paramref name="plugins"/>.</summary>
    /// <param name="plugins">The plugin collection to which the plugin should be added.</param>
    /// <param name="plugin">The plugin to add.</param>
    /// <returns></returns>
    public static IKernelBuilderPlugins Add(this IKernelBuilderPlugins plugins, IKernelPlugin plugin)
    {
        Verify.NotNull(plugins);
        Verify.NotNull(plugin);

        plugins.Services.AddSingleton(plugin);

        return plugins;
    }
    #endregion

    #region ImportPlugin/AddFromObject
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
    public static IKernelPlugin AddFromObject(this ICollection<IKernelPlugin> plugins, object target, string? pluginName = null, IServiceProvider? serviceProvider = null)
    {
        Verify.NotNull(plugins);

        IKernelPlugin plugin = KernelPluginFactory.CreateFromObject(target, pluginName, serviceProvider?.GetService<ILoggerFactory>());
        plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and adds it into the plugin collection.</summary>
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="KernelFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static IKernelBuilderPlugins AddFromObject(this IKernelBuilderPlugins plugins, object target, string? pluginName = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton(serviceProvider => KernelPluginFactory.CreateFromObject(target, pluginName, serviceProvider?.GetService<ILoggerFactory>()));

        return plugins;
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
        Verify.NotNull(kernel);

        return CreatePluginFromPromptDirectory(pluginDirectory, pluginName, promptTemplateFactory, kernel.Services);
    }

    /// <summary>Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>.</summary>
    private static KernelPlugin CreatePluginFromPromptDirectory(
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null,
        IServiceProvider? services = null)
    {
        const string ConfigFile = "config.json";
        const string PromptFile = "skprompt.txt";

        Verify.DirectoryExists(pluginDirectory);
        pluginName ??= new DirectoryInfo(pluginDirectory).Name;

        ILoggerFactory loggerFactory = services?.GetService<ILoggerFactory>() ?? NullLoggerFactory.Instance;

        var factory = promptTemplateFactory ?? new KernelPromptTemplateFactory(loggerFactory);

        KernelPlugin plugin = new(pluginName);
        ILogger logger = loggerFactory.CreateLogger(typeof(Kernel));

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

            plugin.AddFunction(KernelFunctionFactory.CreateFromPrompt(promptTemplateInstance, promptConfig, loggerFactory));
        }

        return plugin;
    }
    #endregion

    #region ImportPlugin/AddFromPromptDirectory
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

    /// <summary>
    /// Creates a plugin containing one function per child directory of the specified <paramref name="pluginDirectory"/>
    /// and adds it into the plugin collection.
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
    /// <param name="plugins">The plugin collection to which the new plugin should be added.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>A list of all the prompt functions found in the directory, indexed by plugin name.</returns>
    public static IKernelBuilderPlugins AddFromPromptDirectory(
        this IKernelBuilderPlugins plugins,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(plugins);

        plugins.Services.AddSingleton<IKernelPlugin>(services =>
            CreatePluginFromPromptDirectory(pluginDirectory, pluginName, promptTemplateFactory, services));

        return plugins;
    }
    #endregion

    #region InvokePromptAsync
    /// <summary>
    /// Invokes a prompt specified via a prompt template.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Plain language definition of the prompt, using SK prompt template language</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="promptTemplateFactory">The template factory to use to interpret <paramref name="promptTemplate"/>.</param>
    /// <returns>The result of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunction">The function failed to invoke successfully.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
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
    /// Invokes a prompt specified via a prompt template and streams its results.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="promptTemplate">Plain language definition of the prompt, using SK prompt template language</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="promptTemplateFactory">The template factory to use to interpret <paramref name="promptTemplate"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>An <see cref="IAsyncEnumerable{T}"/> for streaming the results of the function's invocation.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="kernel"/> is null.</exception>
    /// <exception cref="ArgumentNullException"><paramref name="promptTemplate"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="promptTemplate"/> is empty or composed entirely of whitespace.</exception>
    /// <remarks>
    /// The function will not be invoked until an enumerator is retrieved from the returned <see cref="IAsyncEnumerable{T}"/>
    /// and its iteration initiated via an initial call to <see cref="IAsyncEnumerator{T}.MoveNextAsync"/>.
    /// </remarks>
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

    #region InvokeAsync<T>
    /// <summary>
    /// Invokes the <see cref="KernelFunction"/>.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="function">The <see cref="KernelFunction"/> to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The provided generic typed result value of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="function"/> is null.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <remarks>
    /// This behaves identically to invoking the specified <paramref name="function"/> with this <see cref="Kernel"/> as its <see cref="Kernel"/> argument.
    /// </remarks>
    public static async Task<TResult?> InvokeAsync<TResult>(
        this Kernel kernel,
        KernelFunction function,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
        => (await kernel.InvokeAsync(function, arguments, cancellationToken).ConfigureAwait(false)).GetValue<TResult>();

    /// <summary>
    /// Invokes a function from <see cref="Kernel.Plugins"/> using the specified arguments.
    /// </summary>
    /// <param name="kernel">The <see cref="Kernel"/> containing services, plugins, and other state for use throughout the operation.</param>
    /// <param name="pluginName">The name of the plugin containing the function to invoke. If null, all plugins will be searched for the first function of the specified name.</param>
    /// <param name="functionName">The name of the function to invoke.</param>
    /// <param name="arguments">The arguments to pass to the function's invocation, including any <see cref="PromptExecutionSettings"/>.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The provided generic typed result value of the function's execution.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="functionName"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="functionName"/> is composed entirely of whitespace.</exception>
    /// <exception cref="KernelFunctionCanceledException">The <see cref="KernelFunction"/>'s invocation was canceled.</exception>
    /// <remarks>
    /// This behaves identically to using <see cref="IKernelPluginExtensions.GetFunction"/> to find the desired <see cref="KernelFunction"/> and then
    /// invoking it with this <see cref="Kernel"/> as its <see cref="Kernel"/> argument.
    /// </remarks>
    public static async Task<TResult?> InvokeAsync<TResult>(
        this Kernel kernel,
        string? pluginName,
        string functionName,
        KernelArguments? arguments = null,
        CancellationToken cancellationToken = default)
        => (await kernel.InvokeAsync(pluginName, functionName, arguments, cancellationToken).ConfigureAwait(false)).GetValue<TResult>();
    #endregion

    #region AddKernel for IServiceCollection
    /// <summary>Adds a <see cref="KernelPluginCollection"/> and <see cref="Kernel"/> services to the services collection.</summary>
    /// <param name="services">The service collection.</param>
    /// <returns>
    /// A <see cref="IKernelBuilder"/> that can be used to add additional services to the same <see cref="IServiceCollection"/>.
    /// </returns>
    /// <remarks>
    /// Both services are registered as transient, as both objects are mutable.
    /// The builder returned from this method may be used to add additional plugins and services,
    /// but it may not be used for <see cref="IKernelBuilder.Build"/>: doing so would build the
    /// entire service provider from <paramref name="services"/>.
    /// </remarks>
    public static IKernelBuilder AddKernel(this IServiceCollection services)
    {
        Verify.NotNull(services);

        // Register a KernelPluginCollection to be populated with any IKernelPlugins that have been
        // directly registered in DI. It's transient because the Kernel will store the collection
        // directly, and we don't want two Kernel instances to hold on to the same mutable collection.
        services.AddTransient<KernelPluginCollection>();

        // Register the Kernel as transient. It's mutable and expected to be mutated by consumers,
        // such as via adding event handlers, adding plugins, storing state in its Data collection, etc.
        services.AddTransient<Kernel>();

        // Create and return a builder that can be used for adding services and plugins
        // to the IServiceCollection.
        return new KernelBuilder(services);
    }
    #endregion
}
