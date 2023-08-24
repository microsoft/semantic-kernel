// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.AI.TextCompletion;
using Microsoft.SemanticKernel.Events;
using Microsoft.SemanticKernel.Orchestration;

namespace Microsoft.SemanticKernel.SkillDefinition;

/// <summary>
/// Standard Semantic Kernel callable function with instrumentation.
/// </summary>
public sealed class InstrumentedSKFunction : ISKFunction
{
    /// <inheritdoc/>
    public string Name => this._function.Name;

    /// <inheritdoc/>
    public string SkillName => this._function.SkillName;

    /// <inheritdoc/>
    public string Description => this._function.Description;

    /// <inheritdoc/>
    public bool IsSemantic => this._function.IsSemantic;

    /// <inheritdoc/>
    public CompleteRequestSettings RequestSettings => this._function.RequestSettings;

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
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(InstrumentedSKFunction)) : NullLogger.Instance;

        this._executionTimeHistogram = s_meter.CreateHistogram<double>(
            name: $"SK.{this.SkillName}.{this.Name}.ExecutionTime",
            unit: "ms",
            description: "Duration of function execution");

        this._executionTotalCounter = s_meter.CreateCounter<int>(
            name: $"SK.{this.SkillName}.{this.Name}.ExecutionTotal",
            description: "Total number of function executions");

        this._executionSuccessCounter = s_meter.CreateCounter<int>(
            name: $"SK.{this.SkillName}.{this.Name}.ExecutionSuccess",
            description: "Number of successful function executions");

        this._executionFailureCounter = s_meter.CreateCounter<int>(
            name: $"SK.{this.SkillName}.{this.Name}.ExecutionFailure",
            description: "Number of failed function executions");
    }

    /// <inheritdoc/>
    public FunctionView Describe() =>
        this._function.Describe();

    /// <inheritdoc/>
    public async Task<SKContext> InvokeAsync(
        SKContext context,
        CompleteRequestSettings? settings = null,
        CancellationToken cancellationToken = default)
    {
        return await this.InvokeWithInstrumentationAsync(() =>
            this._function.InvokeAsync(context, settings, cancellationToken)).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(CompleteRequestSettings settings) =>
        this._function.SetAIConfiguration(settings);

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory) =>
        this._function.SetAIService(serviceFactory);

    /// <inheritdoc/>
    public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills) =>
        this._function.SetDefaultSkillCollection(skills);

    /// <inheritdoc/>
    public Task<FunctionInvokingEventArgs> PrepareFunctionInvokingEventArgsAsync(SKContext context) =>
        this._function.PrepareFunctionInvokingEventArgsAsync(context);

    /// <inheritdoc/>
    public Task<FunctionInvokedEventArgs> PrepareFunctionInvokedEventArgsAsync(SKContext context) =>
        this._function.PrepareFunctionInvokedEventArgsAsync(context);

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
        using var activity = s_activitySource.StartActivity($"{this.SkillName}.{this.Name}");

        this._logger.LogInformation("{SkillName}.{FunctionName}: Function execution started.", this.SkillName, this.Name);

        var stopwatch = new Stopwatch();

        stopwatch.Start();

        var result = await func().ConfigureAwait(false);

        stopwatch.Stop();

        if (result.ErrorOccurred)
        {
            this._logger.LogWarning("{SkillName}.{FunctionName}: Function execution status: {Status}",
                this.SkillName, this.Name, "Failed");

            this._logger.LogError(result.LastException, "{SkillName}.{FunctionName}: Function execution exception details: {Message}",
                this.SkillName, this.Name, result.LastException?.Message);

            this._executionFailureCounter.Add(1);
        }
        else
        {
            this._logger.LogInformation("{SkillName}.{FunctionName}: Function execution status: {Status}",
                this.SkillName, this.Name, "Success");

            this._logger.LogInformation("{SkillName}.{FunctionName}: Function execution finished in {ExecutionTime}ms",
                this.SkillName, this.Name, stopwatch.ElapsedMilliseconds);

            this._executionSuccessCounter.Add(1);
        }

        this._executionTotalCounter.Add(1);
        this._executionTimeHistogram.Record(stopwatch.ElapsedMilliseconds);

        return result;
    }

    #endregion
}
