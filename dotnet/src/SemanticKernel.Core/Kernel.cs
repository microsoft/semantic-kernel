// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Globalization;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
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
    public ISKPluginCollection Plugins { get; }

    /// <summary>
    /// Return a new instance of the kernel builder, used to build and configure kernel instances.
    /// </summary>
    [Obsolete("This field will be removed in a future release. Initialize KernelBuilder through constructor instead (new KernelBuilder()).")]
    public static KernelBuilder Builder => new();

    /// <inheritdoc/>
    public IDelegatingHandlerFactory HttpHandlerFactory { get; }

    /// <inheritdoc/>
    public event EventHandler<FunctionInvokingEventArgs>? FunctionInvoking;

    /// <inheritdoc/>
    public event EventHandler<FunctionInvokedEventArgs>? FunctionInvoked;

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="promptTemplateEngine">Prompt template engine</param>
    /// <param name="memory">Semantic text Memory</param>
    /// <param name="httpHandlerFactory">HTTP handler factory</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="serviceSelector">AI Service selector</param>
    [Obsolete("Use IPromptTemplateFactory instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public Kernel(
        ISKPluginCollection plugins,
        IAIServiceProvider aiServiceProvider,
        IPromptTemplateEngine? promptTemplateEngine,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory? loggerFactory,
        IAIServiceSelector? serviceSelector = null) : this(plugins, aiServiceProvider, memory, httpHandlerFactory, loggerFactory, serviceSelector)
    {
        this.PromptTemplateEngine = promptTemplateEngine;
    }

    /// <summary>
    /// Kernel constructor. See KernelBuilder for an easier and less error prone approach to create kernel instances.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="aiServiceProvider">AI Service Provider</param>
    /// <param name="memory">Semantic text Memory</param>
    /// <param name="httpHandlerFactory">HTTP handler factory</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="serviceSelector">AI Service selector</param>
    public Kernel(
        ISKPluginCollection plugins,
        IAIServiceProvider aiServiceProvider,
        ISemanticTextMemory memory,
        IDelegatingHandlerFactory httpHandlerFactory,
        ILoggerFactory? loggerFactory,
        IAIServiceSelector? serviceSelector = null)
    {
        loggerFactory ??= NullLoggerFactory.Instance;

        this.LoggerFactory = loggerFactory;
        this.HttpHandlerFactory = httpHandlerFactory;
        this._memory = memory;
        this._aiServiceProvider = aiServiceProvider;
        this.Plugins = plugins;
        this._aiServiceSelector = serviceSelector ?? new OrderedIAIServiceSelector();

        this._logger = loggerFactory.CreateLogger(typeof(Kernel));
    }

    /// <inheritdoc/>
    [EditorBrowsable(EditorBrowsableState.Never)]
    [Obsolete("This will be removed in a future release. Use RegisterPlugin instead.")]
    public ISKFunction RegisterCustomFunction(ISKFunction customFunction)
    {
        Verify.NotNull(customFunction);

        this.Plugins.Add(new SKPlugin($"plugin{Guid.NewGuid():N}", new[] { customFunction }));

        return customFunction;
    }

    /// <inheritdoc/>
    public async Task<KernelResult> RunAsync(ContextVariables variables, CancellationToken cancellationToken, params ISKFunction[] pipeline)
    {
        var context = this.CreateNewContext(variables);

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

                functionResult = await skFunction.InvokeAsync(context, null, cancellationToken: cancellationToken).ConfigureAwait(false);

                if (this.IsCancelRequested(skFunction, functionResult.Context, pipelineStepCount))
                {
                    break;
                }

                if (this.IsSkipRequested(skFunction, functionResult.Context, pipelineStepCount))
                {
                    continue;
                }

                // Only non-stop results are considered as Kernel results
                allFunctionResults.Add(functionResult!);

                if (this.IsRepeatRequested(skFunction, functionResult.Context, pipelineStepCount))
                {
                    goto repeat;
                }
            }
            catch (Exception ex)
            {
                this._logger.LogError("Function {Function} call fail during pipeline step {Step} with error {Error}:", skFunction.Name, pipelineStepCount, ex.Message);
                throw;
            }

            pipelineStepCount++;
        }

        return KernelResult.FromFunctionResults(allFunctionResults.LastOrDefault()?.Value, allFunctionResults);
    }

    /// <inheritdoc/>
    public SKContext CreateNewContext(
        ContextVariables? variables = null,
        IReadOnlySKPluginCollection? plugins = null,
        ILoggerFactory? loggerFactory = null,
        CultureInfo? culture = null)
    {
        return new SKContext(
            new FunctionRunner(this),
            this._aiServiceProvider,
            this._aiServiceSelector,
            variables,
            plugins ?? this.Plugins,
            new EventHandlerWrapper<FunctionInvokingEventArgs>(this.FunctionInvoking),
            new EventHandlerWrapper<FunctionInvokedEventArgs>(this.FunctionInvoked),
            loggerFactory ?? this.LoggerFactory,
            culture);
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
    }

    #region private ================================================================================
    private ISemanticTextMemory _memory;
    private readonly IAIServiceProvider _aiServiceProvider;
    private readonly IAIServiceSelector _aiServiceSelector;
    private readonly ILogger _logger;

    /// <summary>
    /// Checks if the handler requested to skip the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <returns></returns>
    private bool IsSkipRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount)
    {
        if (KernelFunctionFromPrompt.IsInvokingSkipRequested(context))
        {
            this._logger.LogInformation("Execution was skipped on function invoking event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
            return true;
        }

        return false;
    }

    /// <summary>
    /// Checks if the handler requested to cancel the function execution.
    /// </summary>
    /// <param name="skFunction">Target function</param>
    /// <param name="context">Context of execution</param>
    /// <param name="pipelineStepCount">Current pipeline step</param>
    /// <returns></returns>
    private bool IsCancelRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount)
    {
        if (KernelFunctionFromPrompt.IsInvokingCancelRequested(context))
        {
            this._logger.LogInformation("Execution was cancelled on function invoking event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
            return true;
        }

        if (KernelFunctionFromPrompt.IsInvokedCancelRequested(context))
        {
            this._logger.LogInformation("Execution was cancelled on function invoked event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
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
    /// <returns></returns>
    private bool IsRepeatRequested(ISKFunction skFunction, SKContext context, int pipelineStepCount)
    {
        if (context.FunctionInvokedHandler?.EventArgs?.IsRepeatRequested ?? false)
        {
            this._logger.LogInformation("Execution repeat request on function invoked event of pipeline step {StepCount}: {FunctionName}.", pipelineStepCount, skFunction.Name);
            return true;
        }
        return false;
    }

    #endregion

    #region Obsolete ===============================================================================

    /// <inheritdoc/>
    [Obsolete("Use IPromptTemplateFactory instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public IPromptTemplateEngine? PromptTemplateEngine { get; }

    /// <inheritdoc/>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. See sample dotnet/samples/KernelSyntaxExamples/Example14_SemanticMemory.cs in the semantic-kernel repository.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISemanticTextMemory Memory => this._memory;

    /// <inheritdoc/>
    [Obsolete("Memory functionality will be placed in separate Microsoft.SemanticKernel.Plugins.Memory package. This will be removed in a future release. See sample dotnet/samples/KernelSyntaxExamples/Example14_SemanticMemory.cs in the semantic-kernel repository.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public void RegisterMemory(ISemanticTextMemory memory)
    {
        this._memory = memory;
    }
    #endregion
}
