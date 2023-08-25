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
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Standard Semantic Kernel callable plan with instrumentation.
/// </summary>
public sealed class InstrumentedPlan : IPlan
{
    /// <inheritdoc/>
    public string Name => this._plan.Name;

    /// <inheritdoc/>
    public string SkillName => this._plan.SkillName;

    /// <inheritdoc/>
    public string Description => this._plan.Description;

    /// <inheritdoc/>
    public bool IsSemantic => this._plan.IsSemantic;

    /// <inheritdoc/>
    public CompleteRequestSettings RequestSettings => this._plan.RequestSettings;

    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedPlan"/> class.
    /// </summary>
    /// <param name="plan">Instance of <see cref="IPlan"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public InstrumentedPlan(
        IPlan plan,
        ILoggerFactory? loggerFactory = null)
    {
        this._plan = plan;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(nameof(InstrumentedPlan)) : NullLogger.Instance;
    }

    /// <inheritdoc/>
    public FunctionView Describe()
    {
        return this._plan.Describe();
    }

    /// <inheritdoc/>
    public async Task<SKContext> InvokeAsync(
        SKContext context,
        CompleteRequestSettings? settings = null,
        CancellationToken cancellationToken = default)
    {
        return await this.InvokeWithInstrumentationAsync(() =>
            this._plan.InvokeAsync(context, settings, cancellationToken)).ConfigureAwait(false);
    }

    /// <inheritdoc/>
    public ISKFunction SetAIConfiguration(CompleteRequestSettings settings) =>
        this._plan.SetAIConfiguration(settings);

    /// <inheritdoc/>
    public ISKFunction SetAIService(Func<ITextCompletion> serviceFactory) =>
        this._plan.SetAIService(serviceFactory);

    /// <inheritdoc/>
    public ISKFunction SetDefaultSkillCollection(IReadOnlySkillCollection skills) =>
        this._plan.SetDefaultSkillCollection(skills);

    /// <inheritdoc/>
    public Task<FunctionInvokingEventArgs> PrepareArgsAsync(SKContext context, FunctionInvokingEventArgs? eventArgs = null) =>
        this._plan.PrepareArgsAsync(context, eventArgs);

    /// <inheritdoc/>
    public Task<FunctionInvokedEventArgs> PrepareArgsAsync(SKContext context, FunctionInvokedEventArgs? eventArgs = null) =>
        this._plan.PrepareArgsAsync(context, eventArgs);

    #region private ================================================================================

    private readonly IPlan _plan;
    private readonly ILogger _logger;

    /// <summary>
    /// Instance of <see cref="Meter"/> for plan-related metrics.
    /// </summary>
    private static Meter s_meter = new(typeof(Plan).FullName);

    /// <summary>
    /// Instance of <see cref="Histogram{T}"/> to measure and track the time of plan execution.
    /// </summary>
    private static Histogram<double> s_executionTimeHistogram =
        s_meter.CreateHistogram<double>(
            name: "SK.Plan.Execution.ExecutionTime",
            unit: "ms",
            description: "Duration of plan execution");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the total number of plan executions.
    /// </summary>
    private static Counter<int> s_executionTotalCounter =
        s_meter.CreateCounter<int>(
            name: "SK.Plan.Execution.ExecutionTotal",
            description: "Total number of plan executions");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of successful plan executions.
    /// </summary>
    private static Counter<int> s_executionSuccessCounter =
        s_meter.CreateCounter<int>(
            name: "SK.Plan.Execution.ExecutionSuccess",
            description: "Number of successful plan executions");

    /// <summary>
    /// Instance of <see cref="Counter{T}"/> to keep track of the number of failed plan executions.
    /// </summary>
    private static Counter<int> s_executionFailureCounter =
        s_meter.CreateCounter<int>(
            name: "SK.Plan.Execution.ExecutionFailure",
            description: "Number of failed plan executions");

    /// <summary>
    /// Wrapper for instrumentation to be used in multiple invocation places.
    /// </summary>
    /// <param name="func">Delegate to instrument.</param>
    private async Task<SKContext> InvokeWithInstrumentationAsync(Func<Task<SKContext>> func)
    {
        this._logger.LogInformation("Plan execution started.");

        var stopwatch = new Stopwatch();

        stopwatch.Start();

        var result = await func().ConfigureAwait(false);

        stopwatch.Stop();

        if (result.ErrorOccurred)
        {
            this._logger.LogWarning("Plan execution status: {Status}", "Failed");
            this._logger.LogError(result.LastException, "Plan execution exception details: {Message}", result.LastException?.Message);

            s_executionFailureCounter.Add(1);
        }
        else
        {
            this._logger.LogInformation("Plan execution status: {Status}", "Success");
            this._logger.LogInformation("Plan execution finished in {ExecutionTime}ms", stopwatch.ElapsedMilliseconds);

            s_executionSuccessCounter.Add(1);
        }

        s_executionTotalCounter.Add(1);
        s_executionTimeHistogram.Record(stopwatch.ElapsedMilliseconds);

        return result;
    }

    #endregion
}
