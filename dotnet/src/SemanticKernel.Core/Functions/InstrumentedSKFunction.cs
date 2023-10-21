// Copyright (c) Microsoft. All rights reserved.

using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using the main namespace
namespace Microsoft.SemanticKernel;
#pragma warning restore IDE0130

/// <summary>
/// Standard Semantic Kernel callable function with instrumentation.
/// </summary>
internal sealed class InstrumentedSKFunction : ISKFunction
{
    /// <inheritdoc/>
    public string Name => this._function.Name;

    /// <inheritdoc/>
    public string PluginName => this._function.PluginName;

    /// <inheritdoc/>
    public string Description => this._function.Description;

    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedSKFunction"/> class.
    /// </summary>
    /// <param name="function">Instance of <see cref="ISKFunction"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public InstrumentedSKFunction(
        ISKFunction function,
        ILoggerFactory? loggerFactory = null)
    {
        this._function = function;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(InstrumentedSKFunction)) : NullLogger.Instance;

        this._executionTimeHistogram = s_meter.CreateHistogram<double>(
            name: $"SK.{this.PluginName}.{this.Name}.ExecutionTime",
            unit: "ms",
            description: "Duration of function execution");

        this._executionTotalCounter = s_meter.CreateCounter<int>(
            name: $"SK.{this.PluginName}.{this.Name}.ExecutionTotal",
            description: "Total number of function executions");

        this._executionSuccessCounter = s_meter.CreateCounter<int>(
            name: $"SK.{this.PluginName}.{this.Name}.ExecutionSuccess",
            description: "Number of successful function executions");

        this._executionFailureCounter = s_meter.CreateCounter<int>(
            name: $"SK.{this.PluginName}.{this.Name}.ExecutionFailure",
            description: "Number of failed function executions");
    }

    /// <inheritdoc/>
    public FunctionView Describe() =>
        this._function.Describe();

    /// <inheritdoc/>
    public async Task<FunctionResult> InvokeAsync(
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        return await this.InvokeWithInstrumentationAsync(() =>
            this._function.InvokeAsync(context, requestSettings, cancellationToken)).ConfigureAwait(false);
    }

    #region private ================================================================================

    private readonly ISKFunction _function;
    private readonly ILogger _logger;

    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for function-related activities.
    /// </summary>
    private static readonly ActivitySource s_activitySource = new(typeof(SKFunction).FullName);

    /// <summary>
    /// Instance of <see cref="Meter"/> for function-related metrics.
    /// </summary>
    private static readonly Meter s_meter = new(typeof(SKFunction).FullName);

    /// <summary>
    /// Instance of <see cref="Histogram{T}"/> to measure and track the time of function execution.
    /// </summary>
    private readonly Histogram<double> _executionTimeHistogram;

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of function executions.
    /// </summary>
    private readonly Counter<int> _executionTotalCounter;

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of successful function executions.
    /// </summary>
    private readonly Counter<int> _executionSuccessCounter;

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of failed function executions.
    /// </summary>
    private readonly Counter<int> _executionFailureCounter;

    /// <summary>
    /// Wrapper for instrumentation to be used in multiple invocation places.
    /// </summary>
    /// <param name="func">Delegate to instrument.</param>
    private async Task<FunctionResult> InvokeWithInstrumentationAsync(Func<Task<FunctionResult>> func)
    {
        using var activity = s_activitySource.StartActivity($"{this.PluginName}.{this.Name}");

        this._logger.LogInformation("{PluginName}.{FunctionName}: Function execution started.", this.PluginName, this.Name);

        var stopwatch = new Stopwatch();
        stopwatch.Start();

        FunctionResult result;

        try
        {
            result = await func().ConfigureAwait(false);
        }
        catch (Exception ex)
        {
            this._logger.LogWarning("{PluginName}.{FunctionName}: Function execution status: {Status}",
                this.PluginName, this.Name, "Failed");

            this._logger.LogError(ex, "{PluginName}.{FunctionName}: Function execution exception details: {Message}",
                this.PluginName, this.Name, ex.Message);

            this._executionFailureCounter.Add(1);

            throw;
        }
        finally
        {
            stopwatch.Stop();
            this._executionTotalCounter.Add(1);
            this._executionTimeHistogram.Record(stopwatch.ElapsedMilliseconds);
        }

        this._logger.LogInformation("{PluginName}.{FunctionName}: Function execution status: {Status}",
                this.PluginName, this.Name, "Success");

        this._logger.LogInformation("{PluginName}.{FunctionName}: Function execution finished in {ExecutionTime}ms",
            this.PluginName, this.Name, stopwatch.ElapsedMilliseconds);

        this._executionSuccessCounter.Add(1);

        return result;
    }

    #endregion

    #region Obsolete =======================================================================

    /// <inheritdoc/>
    [Obsolete("Use ISKFunction.RequestSettingsFactory instead. This will be removed in a future release.")]
    public AIRequestSettings? RequestSettings => this._function.RequestSettings;

    /// <inheritdoc/>
    [Obsolete("Use ISKFunction.SetAIRequestSettingsFactory instead. This will be removed in a future release.")]
    public ISKFunction SetAIConfiguration(AIRequestSettings? requestSettings) =>
        this._function.SetAIConfiguration(requestSettings);

    /// <inheritdoc/>
    [Obsolete("Use ISKFunction.SetAIServiceFactory instead. This will be removed in a future release.")]
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory) =>
        this._function.SetAIService(serviceFactory);

    /// <inheritdoc/>
    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.PluginName instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public string SkillName => this._function.PluginName;

    /// <inheritdoc/>
    [Obsolete("Kernel no longer differentiates between Semantic and Native functions. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public bool IsSemantic => this._function.IsSemantic;

    /// <inheritdoc/>
    [Obsolete("This method is a nop and will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction SetDefaultSkillCollection(IReadOnlyFunctionCollection skills) => this;

    /// <inheritdoc/>
    [Obsolete("This method is a nop and will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public ISKFunction SetDefaultFunctionCollection(IReadOnlyFunctionCollection functions) => this;

    #endregion
}
