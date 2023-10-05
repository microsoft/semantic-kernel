// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Reflection;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Http;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.Services;
using Microsoft.SemanticKernel.TemplateEngine;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Semantic kernel class.
/// The kernel provides a function collection to define native and semantic functions, an orchestrator to execute a list of functions.
/// Semantic functions are automatically rendered and executed using an internal prompt template rendering engine.
/// Future versions will allow to:
/// * customize the rendering engine
/// * include branching logic in the functions pipeline
/// * persist execution state for long running pipelines
/// * distribute pipelines over a network
/// * RPC functions and secure environments, e.g. sandboxing and credentials management
/// * auto-generate pipelines given a higher level goal
/// </summary>
public sealed class Kernel : IKernel, IDisposable
{
    /// <inheritdoc/>
    public ILoggerFactory LoggerFactory { get; }

    /// <inheritdoc/>
    public ISemanticTextMemory Memory => this._memory;

    /// <inheritdoc/>
    public IReadOnlyFunctionCollection Functions => this._functionCollection;

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use Kernel.Functions instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public IReadOnlyFunctionCollection Skills => this._functionCollection;
#pragma warning restore CS1591

    /// <inheritdoc/>
    public IPromptTemplateEngine PromptTemplateEngine { get; }

    /// <summary>
    /// Return a new instance of the kernel builder, used to build and configure kernel instances.
    /// </summary>
    public static KernelBuilder Builder => new();

    /// <inheritdoc/>
    public IDelegatingHandlerFactory HttpHandlerFactory => this._httpHandlerFactory;

    /// <inheritdoc/>
    public event EventHandler<FunctionInvokingEventArgs>? FunctionInvoking;

    /// <inheritdoc/>
    public event EventHandler<FunctionInvokedEventArgs>? FunctionInvoked;

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="functionCollection">function collection</param>
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="promptTemplateEngine">Prompt template engine</param>
    /// <param name="memory">Semantic text Memory</param>
    /// <param name="httpHandlerFactory"></param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public Kernel(
        IFunctionCollection functionCollection,
        IAIServiceProvider aiServiceProvider,
        IPromptTemplateEngine promptTemplateEngine,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory loggerFactory)
    {
        this.LoggerFactory = loggerFactory;
        this._httpHandlerFactory = httpHandlerFactory;
        this.PromptTemplateEngine = promptTemplateEngine;
        this._memory = memory;
        this._aiServiceProvider = aiServiceProvider;
        this._promptTemplateEngine = promptTemplateEngine;
        this._functionCollection = functionCollection;

        this._logger = loggerFactory.CreateLogger(typeof(Kernel));
    }

    /// <inheritdoc/>
    public IDictionary<string, ISKFunction> ImportFunctions(object functionsInstance, string? pluginName = null)
    {
        Verify.NotNull(functionsInstance);

        if (string.IsNullOrWhiteSpace(pluginName))
        {
            pluginName = FunctionCollection.GlobalFunctionsPluginName;
            this._logger.LogTrace("Importing functions from {0} to the global plugin namespace", functionsInstance.GetType().FullName);
        }
        else
        {
            this._logger.LogTrace("Importing functions from {0} to the {1} namespace", functionsInstance.GetType().FullName, pluginName);
        }

        Dictionary<string, ISKFunction> functions = ImportFunctions(
            functionsInstance,
            pluginName!,
            this._logger,
            this.LoggerFactory
        );
        foreach (KeyValuePair<string, ISKFunction> f in functions)
        {
            f.Value.SetDefaultFunctionCollection(this.Functions);
            this._functionCollection.AddFunction(f.Value);
        }

        return functions;
    }

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use Kernel.ImportFunctions instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public IDictionary<string, ISKFunction> ImportSkill(object functionsInstance, string? pluginName = null)
    {
        return this.ImportFunctions(functionsInstance, pluginName);
    }
#pragma warning restore CS1591

    /// <inheritdoc/>
    public ISKFunction RegisterCustomFunction(ISKFunction customFunction)
    {
        Verify.NotNull(customFunction);

        customFunction.SetDefaultFunctionCollection(this.Functions);
        this._functionCollection.AddFunction(customFunction);

        return customFunction;
    }

    /// <inheritdoc/>
    public void RegisterMemory(ISemanticTextMemory memory)
    {
        this._memory = memory;
    }

    /// <inheritdoc/>
    public Task<KernelResult> RunAsync(ISKFunction skFunction,
        ContextVariables? variables = null,
        CancellationToken cancellationToken = default)
        => this.RunAsync(variables ?? new(), cancellationToken, skFunction);

    /// <inheritdoc/>
    public Task<KernelResult> RunAsync(params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(), pipeline);

    /// <inheritdoc/>
    public Task<KernelResult> RunAsync(string input, params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(input), pipeline);

    /// <inheritdoc/>
    public Task<KernelResult> RunAsync(ContextVariables variables, params ISKFunction[] pipeline)
        => this.RunAsync(variables, CancellationToken.None, pipeline);

    /// <inheritdoc/>
    public Task<KernelResult> RunAsync(CancellationToken cancellationToken, params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(), cancellationToken, pipeline);

    /// <inheritdoc/>
    public Task<KernelResult> RunAsync(string input, CancellationToken cancellationToken, params ISKFunction[] pipeline)
        => this.RunAsync(new ContextVariables(input), cancellationToken, pipeline);

    /// <inheritdoc/>
    public async Task<KernelResult> RunAsync(ContextVariables variables, CancellationToken cancellationToken, params ISKFunction[] pipeline)
    {
        var context = new SKContext(this, variables);

        FunctionResult? functionResult = null;

        int pipelineStepCount = 0;
        var allFunctionResults = new List<FunctionResult>();

        foreach (ISKFunction skFunction in pipeline)
        {
repeat:
            cancellationToken.ThrowIfCancellationRequested();

            try
            {
                var functionDetails = skFunction.Describe();

                var functionInvokingArgs = this.OnFunctionInvoking(functionDetails, context);
                if (functionInvokingArgs?.CancelToken.IsCancellationRequested ?? false)
                {
                    this._logger.LogInformation("Execution was cancelled on function invoking event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
                    break;
                }

                if (functionInvokingArgs?.IsSkipRequested ?? false)
                {
                    this._logger.LogInformation("Execution was skipped on function invoking event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
                    continue;
                }

                functionResult = await skFunction.InvokeAsync(context, cancellationToken: cancellationToken).ConfigureAwait(false);

                context = functionResult.Context;

                var functionInvokedArgs = this.OnFunctionInvoked(functionDetails, functionResult);

                if (functionInvokedArgs is not null)
                {
                    // All changes to the SKContext by invoked handlers may reflect in the original function result
                    functionResult = new FunctionResult(functionDetails.Name, functionDetails.PluginName, functionInvokedArgs.SKContext, functionInvokedArgs.SKContext.Result);
                }

                allFunctionResults.Add(functionResult);

                if (functionInvokedArgs?.CancelToken.IsCancellationRequested ?? false)
                {
                    this._logger.LogInformation("Execution was cancelled on function invoked event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
                    break;
                }

                if (functionInvokedArgs?.IsRepeatRequested ?? false)
                {
                    this._logger.LogInformation("Execution repeat request on function invoked event of pipeline step {StepCount}: {PluginName}.{FunctionName}.", pipelineStepCount, skFunction.PluginName, skFunction.Name);
                    goto repeat;
                }
            }
            catch (Exception ex)
            {
                this._logger.LogError("Plugin {Plugin} function {Function} call fail during pipeline step {Step} with error {Error}:", skFunction.PluginName, skFunction.Name, pipelineStepCount, ex.Message);
                throw;
            }

            pipelineStepCount++;
        }

        return KernelResult.FromFunctionResults(functionResult?.Value, allFunctionResults);
    }

    /// <inheritdoc/>
    public SKContext CreateNewContext()
    {
        return new SKContext(
            this,
            functions: this._functionCollection);
    }

    /// <inheritdoc/>
    public T GetService<T>(string? name = null) where T : IAIService
    {
        var service = this._aiServiceProvider.GetService<T>(name);
        if (service != null)
        {
            return service;
        }

        throw new SKException($"Service of type {typeof(T)} and name {name ?? "<NONE>"} not registered.");
    }

    /// <summary>
    /// Dispose of resources.
    /// </summary>
    public void Dispose()
    {
        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._memory is IDisposable mem) { mem.Dispose(); }

        // ReSharper disable once SuspiciousTypeConversion.Global
        if (this._functionCollection is IDisposable reg) { reg.Dispose(); }
    }

    #region private ================================================================================

    private readonly IFunctionCollection _functionCollection;
    private ISemanticTextMemory _memory;
    private readonly IPromptTemplateEngine _promptTemplateEngine;
    private readonly IAIServiceProvider _aiServiceProvider;
    private readonly ILogger _logger;
    private readonly IDelegatingHandlerFactory _httpHandlerFactory;

    /// <summary>
    /// Execute the OnFunctionInvoking event handlers.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="context">SKContext before function invocation</param>
    /// <returns>FunctionInvokingEventArgs if the event was handled, null otherwise</returns>
    private FunctionInvokingEventArgs? OnFunctionInvoking(FunctionView functionView, SKContext context)
    {
        if (this.FunctionInvoking is not null)
        {
            var args = new FunctionInvokingEventArgs(functionView, context);
            this.FunctionInvoking.Invoke(this, args);

            return args;
        }

        return null;
    }

    /// <summary>
    /// Execute the OnFunctionInvoked event handlers.
    /// </summary>
    /// <param name="functionView">Function view details</param>
    /// <param name="result">Function result after invocation</param>
    /// <returns>FunctionInvokedEventArgs if the event was handled, null otherwise</returns>
    private FunctionInvokedEventArgs? OnFunctionInvoked(FunctionView functionView, FunctionResult result)
    {
        if (this.FunctionInvoked is not null)
        {
            var args = new FunctionInvokedEventArgs(functionView, result);
            this.FunctionInvoked.Invoke(this, args);

            return args;
        }

        return null;
    }

    /// <summary>
    /// Import a native functions into the kernel function collection, so that semantic functions and pipelines can consume its functions.
    /// </summary>
    /// <param name="pluginInstance">Class instance from which to import available native functions</param>
    /// <param name="pluginName">Plugin name, used to group functions under a shared namespace</param>
    /// <param name="logger">Application logger</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <returns>Dictionary of functions imported from the given class instance, case-insensitively indexed by name.</returns>
    private static Dictionary<string, ISKFunction> ImportFunctions(object pluginInstance, string pluginName, ILogger logger, ILoggerFactory loggerFactory)
    {
        MethodInfo[] methods = pluginInstance.GetType().GetMethods(BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public);
        logger.LogTrace("Importing plugin name: {0}. Potential methods found: {1}", pluginName, methods.Length);

        // Filter out non-SKFunctions and fail if two functions have the same name
        Dictionary<string, ISKFunction> result = new(StringComparer.OrdinalIgnoreCase);
        foreach (MethodInfo method in methods)
        {
            if (method.GetCustomAttribute<SKFunctionAttribute>() is not null)
            {
                ISKFunction function = SKFunction.FromNativeMethod(method, pluginInstance, pluginName, loggerFactory);
                if (result.ContainsKey(function.Name))
                {
                    throw new SKException("Function overloads are not supported, please differentiate function names");
                }

                result.Add(function.Name, function);
            }
        }

        logger.LogTrace("Methods imported {0}", result.Count);

        return result;
    }

    #endregion

    #region Obsolete ===============================================================================

    /// <inheritdoc/>
    [Obsolete("Func shorthand no longer no longer supported. Use Kernel.Functions collection instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction Func(string pluginName, string functionName)
    {
        return this.Functions.GetFunction(pluginName, functionName);
    }

    #endregion
}
