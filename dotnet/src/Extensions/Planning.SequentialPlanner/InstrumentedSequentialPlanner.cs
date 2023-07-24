// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Globalization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Instrumented planner that uses semantic function to create a sequential plan.
/// Captures planner-related logs and metrics.
/// </summary>
public sealed class InstrumentedSequentialPlanner : ISequentialPlanner, IDisposable
{
    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedSequentialPlanner"/> class.
    /// </summary>
    /// <param name="planner">Instance of <see cref="ISequentialPlanner"/> to decorate.</param>
    /// <param name="logger">Optional logger.</param>
    public InstrumentedSequentialPlanner(
        ISequentialPlanner planner,
        ILogger? logger = null)
    {
        this._planner = planner;
        this._logger = logger ?? NullLogger.Instance;

        string telemetryPrefixName = this.PlanName ?? this.GetType().Name;
        this.s_activitySource = new(telemetryPrefixName);
        this.s_executionTimeHistogram = s_meter.CreateHistogram<double>(
            name: string.Format(CultureInfo.InvariantCulture, executionTimeMetricFormat, telemetryPrefixName),
            unit: "ms",
            description: "Planner execution time");
        this.s_executionTotalCounter = s_meter.CreateCounter<int>(
            name: string.Format(CultureInfo.InvariantCulture, executionTotalMetricFormat, telemetryPrefixName),
            unit: "Executions",
            description: "Total planner execution counter");
        this.s_executionSuccessCounter = s_meter.CreateCounter<int>(
            name: string.Format(CultureInfo.InvariantCulture, executionSuccessMetricFormat, telemetryPrefixName),
            unit: "Executions",
            description: "Success planner execution counter");
        this.s_executionFailureCounter = s_meter.CreateCounter<int>(
            name: string.Format(CultureInfo.InvariantCulture, executionCountFailureMetricFormat, telemetryPrefixName),
            unit: "Executions",
            description: "Failure planner execution counter");
    }

    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        using var activity = this.s_activitySource.StartActivity("SequentialPlanner.CreatePlan");

        this.s_executionTotalCounter.Add(1);
        this._logger.LogInformation("Planner (Plan: {PlanName}) creation started", this.PlanName);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Plan \"{PlanName}\" Goal: {Goal}", this.PlanName, goal);

        var stopwatch = new Stopwatch();
        stopwatch.Start();

        try
        {
            var plan = await this._planner.CreatePlanAsync(goal, cancellationToken).ConfigureAwait(false);

            stopwatch.Stop();

            this.s_executionSuccessCounter.Add(1);
            this.s_executionTimeHistogram.Record(stopwatch.ElapsedMilliseconds);
            this._logger.LogInformation("Plan {Name} creation finished in {ExecutionTime}ms", this.PlanName, stopwatch.ElapsedMilliseconds);
            this._logger.LogInformation("Planner (Plan: {PlanName}) creation status: {Status}", this.PlanName, "Success");
            this._logger.LogInformation("Created plan \"{PlanName}\": \n {Plan}", this.PlanName, plan.ToSafePlanString());
            // Sensitive data, logging as trace, disabled by default
            this._logger.LogTrace("Created plan \"{PlanName}\" with details: \n {Plan}", this.PlanName, plan.ToPlanString());

            return plan;
        }
        catch (Exception ex)
        {
            this.s_executionFailureCounter.Add(1);
            this._logger.LogInformation("Plan (Plan: {PlanName}) creation status: {Status}", this.PlanName, "Failed");
            this._logger.LogError(ex, "Plan (Plan: {PlanName}) creation exception details: {Message}", this.PlanName, ex.Message);

            throw;
        }
    }

    public void Dispose()
    {
        if (this.s_activitySource is not null)
        {
            this.s_activitySource.Dispose();
        }
    }

    public string? PlanName => this._planner.PlanName;

    #region private ================================================================================
    private readonly ISequentialPlanner _planner;
    private readonly ILogger _logger;

    #region Instrumentation
    private const string executionTimeMetricFormat = "SK.SequentialPlanner.{0}.ExecutionTime";
    private const string executionTotalMetricFormat = "SK.SequentialPlanner.{0}.ExecutionTotal";
    private const string executionCountFailureMetricFormat = "SK.SequentialPlanner.{0}.ExecutionFailure";
    private const string executionSuccessMetricFormat = "SK.SequentialPlanner.{0}.ExecutionSuccess";
    private Histogram<double> s_executionTimeHistogram;
    private Counter<int> s_executionTotalCounter;
    private Counter<int> s_executionSuccessCounter;
    private Counter<int> s_executionFailureCounter;

    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for planner-related activities.
    /// </summary>
    private ActivitySource s_activitySource;

    /// <summary>
    /// Instance of <see cref="Meter"/> for planner-related metrics.
    /// </summary>
    private static Meter s_meter = new(nameof(InstrumentedSequentialPlanner));
    #endregion
    #endregion
}
