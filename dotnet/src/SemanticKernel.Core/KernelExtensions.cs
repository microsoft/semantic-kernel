// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.IO;
using System.Linq;
using System.Reflection;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.TemplateEngine;
using Microsoft.SemanticKernel.Text;

namespace Microsoft.SemanticKernel;

/// <summary>Extension methods for interacting with <see cref="Kernel"/>.</summary>
public static class KernelExtensions
{
    #region CreateFunctionFromMethod
    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a method, specified via a delegate.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="method">The method to be represented via the created <see cref="ISKFunction"/>.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="ISKFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static ISKFunction CreateFunctionFromMethod(
        this Kernel kernel,
        Delegate method,
        string? functionName = null,
        string? description = null,
        IEnumerable<SKParameterMetadata>? parameters = null,
        SKReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);

        return SKFunctionFactory.CreateFromMethod(method.Method, method.Target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates an <see cref="ISKFunction"/> instance for a method, specified via an <see cref="MethodInfo"/> instance
    /// and an optional target object if the method is an instance method.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="method">The method to be represented via the created <see cref="ISKFunction"/>.</param>
    /// <param name="target">The target object for the <paramref name="method"/> if it represents an instance method. This should be null if and only if <paramref name="method"/> is a static method.</param>
    /// <param name="functionName">Optional function name. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="description">Optional description of the method. If null, it will default to one derived from the method represented by <paramref name="method"/>, if possible (e.g. via a <see cref="DescriptionAttribute"/> on the method).</param>
    /// <param name="parameters">Optional parameter descriptions. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <param name="returnParameter">Optional return parameter description. If null, it will default to one derived from the method represented by <paramref name="method"/>.</param>
    /// <returns>The created <see cref="ISKFunction"/> wrapper for <paramref name="method"/>.</returns>
    public static ISKFunction CreateFunctionFromMethod(
        this Kernel kernel,
        MethodInfo method,
        object? target = null,
        string? functionName = null,
        string? description = null,
        IEnumerable<SKParameterMetadata>? parameters = null,
        SKReturnParameterMetadata? returnParameter = null)
    {
        Verify.NotNull(kernel);

        return SKFunctionFactory.CreateFromMethod(method, target, functionName, description, parameters, returnParameter, kernel.LoggerFactory);
    }
    #endregion

    #region CreateFunctionFromPrompt
    // TODO: Revise these CreateFunctionFromPrompt method XML comments

    /// <summary>
    /// Creates a string-to-string semantic function, with no direct support for input context.
    /// The function can be referenced in templates and will receive the context, but when invoked programmatically you
    /// can only pass in a string in input and receive a string in output.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="requestSettings">Optional LLM request settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        string promptTemplate,
        AIRequestSettings? requestSettings = null,
        string? functionName = null,
        string? description = null)
    {
        Verify.NotNull(kernel);

        return SKFunctionFactory.CreateFromPrompt(promptTemplate, requestSettings, functionName, description, kernel.LoggerFactory);
    }

    /// <summary>
    /// Creates a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        string promptTemplate,
        PromptTemplateConfig promptTemplateConfig,
        string? functionName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        Verify.NotNull(kernel);

        return SKFunctionFactory.CreateFromPrompt(promptTemplate, promptTemplateConfig, functionName, promptTemplateFactory, kernel.LoggerFactory);
    }

    /// <summary>
    /// Allow to define a semantic function passing in the definition in natural language, i.e. the prompt template.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="promptTemplate">Plain language definition of the semantic function, using SK template language</param>
    /// <param name="promptTemplateConfig">Prompt template configuration.</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <returns>A function ready to use</returns>
    public static ISKFunction CreateFunctionFromPrompt(
        this Kernel kernel,
        IPromptTemplate promptTemplate,
        PromptTemplateConfig promptTemplateConfig,
        string? functionName = null)
    {
        Verify.NotNull(kernel);

        return SKFunctionFactory.CreateFromPrompt(promptTemplate, promptTemplateConfig, functionName, kernel.LoggerFactory);
    }
    #endregion

    #region CreatePluginFromObject
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/>.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The kernel.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="SKFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static ISKPlugin CreatePluginFromObject<T>(this Kernel kernel, string? pluginName = null)
        where T : new()
    {
        Verify.NotNull(kernel);

        return SKPlugin.FromObject<T>(pluginName, kernel.LoggerFactory);
    }

    /// <summary>Creates a plugin that wraps the specified target object.</summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="SKFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static ISKPlugin CreatePluginFromObject(this Kernel kernel, object target, string? pluginName = null)
    {
        Verify.NotNull(kernel);

        return SKPlugin.FromObject(target, pluginName, kernel.LoggerFactory);
    }
    #endregion

    #region ImportPluginFromObject
    /// <summary>Creates a plugin that wraps a new instance of the specified type <typeparamref name="T"/> and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <typeparam name="T">Specifies the type of the object to wrap.</typeparam>
    /// <param name="kernel">The kernel.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <typeparamref name="T"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="SKFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static ISKPlugin ImportPluginFromObject<T>(this Kernel kernel, string? pluginName = null)
        where T : new()
    {
        ISKPlugin plugin = CreatePluginFromObject<T>(kernel, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }

    /// <summary>Creates a plugin that wraps the specified target object and imports it into the <paramref name="kernel"/>'s plugin collection.</summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="target">The instance of the class to be wrapped.</param>
    /// <param name="pluginName">
    /// Name of the plugin for function collection and prompt templates. If the value is null, a plugin name is derived from the type of the <paramref name="target"/>.
    /// </param>
    /// <remarks>
    /// Public methods that have the <see cref="SKFunctionFromPrompt"/> attribute will be included in the plugin.
    /// </remarks>
    public static ISKPlugin ImportPluginFromObject(this Kernel kernel, object target, string? pluginName = null)
    {
        ISKPlugin plugin = CreatePluginFromObject(kernel, target, pluginName);
        kernel.Plugins.Add(plugin);
        return plugin;
    }
    #endregion

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
    /// <param name="kernel">The kernel.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by plugin name.</returns>
    public static ISKPlugin CreatePluginFromPromptDirectory(
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

        SKPlugin plugin = new(pluginName);
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
            var promptTemplateConfig = File.Exists(configPath) ?
                PromptTemplateConfig.FromJson(File.ReadAllText(configPath)) :
                new PromptTemplateConfig();

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Config {0}: {1}", functionName, JsonSerializer.Serialize(promptTemplateConfig, JsonOptionsCache.WriteIndented));
            }

            // Load prompt template
            var promptTemplate = File.ReadAllText(promptPath);
            IPromptTemplate? promptTemplateInstance = factory.Create(promptTemplate, promptTemplateConfig);

            if (logger.IsEnabled(LogLevel.Trace))
            {
                logger.LogTrace("Registering function {0}.{1} loaded from {2}", pluginName, functionName, functionDirectory);
            }

            plugin.AddFunction(kernel.CreateFunctionFromPrompt(promptTemplateInstance, promptTemplateConfig, functionName));
        }

        return plugin;
    }

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
    /// <param name="kernel">The kernel.</param>
    /// <param name="pluginDirectory">Path to the directory containing the plugin, e.g. "/myAppPlugins/StrategyPlugin"</param>
    /// <param name="pluginName">The name of the plugin. If null, the name is derived from the <paramref name="pluginDirectory"/> directory name.</param>
    /// <param name="promptTemplateFactory">Prompt template factory</param>
    /// <returns>A list of all the semantic functions found in the directory, indexed by plugin name.</returns>
    public static ISKPlugin ImportPluginFromPromptDirectory(
        this Kernel kernel,
        string pluginDirectory,
        string? pluginName = null,
        IPromptTemplateFactory? promptTemplateFactory = null)
    {
        ISKPlugin plugin = CreatePluginFromPromptDirectory(kernel, pluginDirectory, pluginName, promptTemplateFactory);
        kernel.Plugins.Add(plugin);
        return plugin;
    }
    #endregion

    #region InvokePromptAsync
    /// <summary>
    /// Invoke a semantic function using the provided prompt template.
    /// </summary>
    /// <param name="kernel">Semantic Kernel instance</param>
    /// <param name="promptTemplate">Plain language definition of the prompt, using SK prompt template language</param>
    /// <param name="requestSettings">Optional LLM request settings</param>
    /// <param name="functionName">A name for the given function. The name can be referenced in templates and used by the pipeline planner.</param>
    /// <param name="description">Optional description, useful for the planner</param>
    /// <returns>Function execution result</returns>
    public static Task<FunctionResult> InvokePromptAsync(
        this Kernel kernel,
        string promptTemplate,
        AIRequestSettings? requestSettings = null,
        string? functionName = null,
        string? description = null) =>
        kernel.RunAsync((ISKFunction)SKFunctionFactory.CreateFromPrompt(
            promptTemplate,
            requestSettings,
            functionName,
            description));
    #endregion

    /// <summary>
    /// Run a single synchronous or asynchronous <see cref="ISKFunction"/>.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="skFunction">A Semantic Kernel function to run</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function</returns>
    public static Task<FunctionResult> RunAsync(
        this Kernel kernel,
        ISKFunction skFunction,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);

        return kernel.RunAsync(variables ?? new(), cancellationToken, skFunction);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<FunctionResult> RunAsync(
        this Kernel kernel,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);

        return kernel.RunAsync(new ContextVariables(), pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="input">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<FunctionResult> RunAsync(
        this Kernel kernel,
        string input,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);

        return kernel.RunAsync(new ContextVariables(input), pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="variables">Input to process</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<FunctionResult> RunAsync(
        this Kernel kernel,
        ContextVariables variables,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);

        return kernel.RunAsync(variables, CancellationToken.None, pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<FunctionResult> RunAsync(
        this Kernel kernel,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);

        return kernel.RunAsync(new ContextVariables(), cancellationToken, pipeline);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="input">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    public static Task<FunctionResult> RunAsync(
        this Kernel kernel,
        string input,
        CancellationToken cancellationToken,
        params ISKFunction[] pipeline)
    {
        Verify.NotNull(kernel);

        return kernel.RunAsync(new ContextVariables(input), cancellationToken, pipeline);
    }

    /// <summary>
    /// Run a plugin function.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="pluginName">The name of the plugin containing the function to run.</param>
    /// <param name="functionName">The name of the function to run.</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Result of the function run.</returns>
    public static Task<FunctionResult> RunAsync(
        this Kernel kernel,
        string pluginName,
        string functionName,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNull(kernel);

        var function = kernel.Plugins.GetFunction(pluginName, functionName);

        return kernel.RunAsync(function, variables, cancellationToken);
    }

    /// <summary>
    /// Run a pipeline composed of synchronous and asynchronous functions.
    /// </summary>
    /// <param name="kernel">The kernel.</param>
    /// <param name="variables">Input to process</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <param name="pipeline">List of functions</param>
    /// <returns>Result of the function composition</returns>
    /// <inheritdoc/>
    public static async Task<FunctionResult> RunAsync(this Kernel kernel, ContextVariables variables, CancellationToken cancellationToken, params ISKFunction[] pipeline)
    {
        var context = kernel.CreateNewContext(variables);

        FunctionResult? functionResult = null;

        int pipelineStepCount = 0;
        var allFunctionResults = new List<FunctionResult>();

        var logger = kernel.LoggerFactory.CreateLogger(typeof(Kernel));

        foreach (ISKFunction skFunction in pipeline)
        {
repeat:
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var functionDetails = skFunction.GetMetadata();

                functionResult = await skFunction.InvokeAsync(kernel, context, null, cancellationToken: cancellationToken).ConfigureAwait(false);

                if (IsCancelRequested(skFunction, functionResult.Context, pipelineStepCount, logger))
                {
                    break;
                }

                if (IsSkipRequested(skFunction, functionResult.Context, pipelineStepCount, logger))
                {
                    continue;
                }

                // Only non-stop results are considered as Kernel results
                allFunctionResults.Add(functionResult!);

                if (IsRepeatRequested(skFunction, functionResult.Context, pipelineStepCount, logger))
                {
                    goto repeat;
                }
            }
            catch (Exception ex)
            {
                logger.LogError("Function {Function} call fail during pipeline step {Step} with error {Error}:", skFunction.Name, pipelineStepCount, ex.Message);
                throw;
            }

            pipelineStepCount++;
        }

        return allFunctionResults.LastOrDefault();
    }

    /// <summary>
    /// Checks if the handler requested to cancel the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <param name="logger">The logger.</param>
    /// <returns></returns>
    private static bool IsCancelRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount, ILogger logger)
    {
        if (SKFunctionFromPrompt.IsInvokingCancelRequested(context))
        {
            logger.LogInformation("Execution was cancelled on function invoking event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
            return true;
        }

        if (SKFunctionFromPrompt.IsInvokedCancelRequested(context))
        {
            logger.LogInformation("Execution was cancelled on function invoked event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
            return true;
        }

        return false;
    }

    /// <summary>
    /// Checks if the handler requested to skip the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <param name="logger">The logger.</param>
    /// <returns></returns>
    private static bool IsSkipRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount, ILogger logger)
    {
        if (SKFunctionFromPrompt.IsInvokingSkipRequested(context))
        {
            logger.LogInformation("Execution was skipped on function invoking event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
            return true;
        }

        return false;
    }

    /// <summary>
    /// Checks if the handler requested to repeat the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <param name="logger">The logger.</param>
    /// <returns></returns>
    private static bool IsRepeatRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount, ILogger logger)
    {
        if (context.FunctionInvokedHandler?.EventArgs?.IsRepeatRequested ?? false)
        {
            logger.LogInformation("Execution repeat request on function invoked event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
            return true;
        }
        return false;
    }
}
