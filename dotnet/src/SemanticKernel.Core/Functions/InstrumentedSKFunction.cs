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
public sealed class InstrumentedSKFunction : ISKFunction
{
    /// <inheritdoc/>
    public string Name => this._function.Name;

    /// <inheritdoc/>
    public string PluginName => this._function.PluginName;

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.PluginName instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public string SkillName => this._function.PluginName;
#pragma warning restore CS1591

    /// <inheritdoc/>
    public string Description => this._function.Description;

    /// <inheritdoc/>
    public AIRequestSettings? RequestSettings => this._function.RequestSettings;

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
    public async Task<SKContext> InvokeAsync(
        SKContext context,
        AIRequestSettings? requestSettings = null,
        CancellationToken cancellationToken = default)
    {
        return await this.InvokeWithInstrumentationAsync(() =>
            this._function.InvokeAsync(context, requestSettings, cancellationToken)).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(AIRequestSettings? requestSettings) =>
        this._function.SetAIConfiguration(requestSettings);

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory) =>
        this._function.SetAIService(serviceFactory);

    /// <inheritdoc/>
    public ISKFunction SetDefaultFunctionCollection(IReadOnlyFunctionCollection functions) =>
        this._function.SetDefaultFunctionCollection(functions);

    [Obsolete("Methods, properties and classes which include Skill in the name have been renamed. Use ISKFunction.SetDefaultFunctionCollection instead. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
#pragma warning disable CS1591
    public ISKFunction SetDefaultSkillCollection(IReadOnlyFunctionCollection skills) =>
        this._function.SetDefaultFunctionCollection(skills);

    #region private ================================================================================

    private readonly ISKFunction _function;
    private readonly ILogger _logger;

    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for function-related activities.
    /// </summary>
    private static ActivitySource s_activitySource = new(typeof(SKFunction).FullName);

    /// <summary>
    /// Instance of <see cref="Meter"/> for function-related metrics.
    /// </summary>
    private static Meter s_meter = new(typeof(SKFunction).FullName);

    /// <summary>
    /// Instance of <see cref="Histogram{T}"/> to measure and track the time of function execution.
    /// </summary>
    private Histogram<double> _executionTimeHistogram;

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of function executions.
    /// </summary>
    private Counter<int> _executionTotalCounter;

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of successful function executions.
    /// </summary>
    private Counter<int> _executionSuccessCounter;

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of failed function executions.
    /// </summary>
    private Counter<int> _executionFailureCounter;

    /// <summary>
    /// Wrapper for instrumentation to be used in multiple invocation places.
    /// </summary>
    /// <param name="func">Delegate to instrument.</param>
    private async Task<SKContext> InvokeWithInstrumentationAsync(Func<Task<SKContext>> func)
    {
        using var activity = s_activitySource.StartActivity($"{this.PluginName}.{this.Name}");

        this._logger.LogInformation("{PluginName}.{FunctionName}: Function execution started.", this.PluginName, this.Name);

        var stopwatch = new Stopwatch();
        stopwatch.Start();

        SKContext result;

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
    [Obsolete("Kernel no longer differentiates between Semantic and Native functions. This will be removed in a future release.")]
    [EditorBrowsable(EditorBrowsableState.Never)]
    public bool IsSemantic => this._function.IsSemantic;

    #endregion
}
