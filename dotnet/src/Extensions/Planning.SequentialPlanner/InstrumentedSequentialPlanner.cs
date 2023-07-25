// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Instrumented planner that uses semantic function to create a sequential plan.
/// Captures planner-related logs and metrics.
/// </summary>
public sealed class InstrumentedSequentialPlanner : ISequentialPlanner
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
    }

    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default)
    {
        using var activity = s_activitySource.StartActivity($"{PlannerType}.CreatePlan");

        s_executionTotalCounter.Add(1);

        this._logger.LogInformation("{PlannerType}: Plan creation started.", PlannerType);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("{PlannerType}: Plan Goal: {Goal}", PlannerType, goal);

        var stopwatch = new Stopwatch();

        try
        {
            stopwatch.Start();

            var plan = await this._planner.CreatePlanAsync(goal, cancellationToken).ConfigureAwait(false);

            stopwatch.Stop();

            s_executionTimeHistogram.Record(stopwatch.ElapsedMilliseconds);

            s_executionSuccessCounter.Add(1);

            this._logger.LogInformation("{PlannerType}: Plan creation status: {Status}", PlannerType, "Success");

            this._logger.LogInformation("{PlannerType}: Created plan: \n {Plan}", PlannerType, plan.ToSafePlanString());

            // Sensitive data, logging as trace, disabled by default
            this._logger.LogTrace("{PlannerType}: Created plan with details: \n {Plan}", PlannerType, plan.ToPlanString());

            return plan;
        }
        catch (Exception ex)
        {
            s_executionFailureCounter.Add(1);

            this._logger.LogInformation("{PlannerType}: Plan creation status: {Status}", PlannerType, "Failed");
            this._logger.LogError(ex, "{PlannerType}: Plan creation exception details: {Message}", PlannerType, ex.Message);

            throw;
        }
        finally
        {
            this._logger.LogInformation("{PlannerType}: Plan creation finished in {ExecutionTime}ms.", PlannerType, stopwatch.ElapsedMilliseconds);
        }
    }

    #region private ================================================================================

    private const string PlannerType = nameof(SequentialPlanner);

    private readonly ISequentialPlanner _planner;
    private readonly ILogger _logger;

    #endregion

    #region Telemetry

    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for planner-related activities.
    /// </summary>
    private static ActivitySource s_activitySource = new(typeof(InstrumentedSequentialPlanner).FullName);

    /// <summary>
    /// Instance of <see cref="Meter"/> for planner-related metrics.
    /// </summary>
    private static Meter s_meter = new(typeof(InstrumentedSequentialPlanner).FullName);

    /// <summary>
    /// Histogram to measure and track the execution time of the plan creation.
    /// </summary>
    private static Histogram<double> s_executionTimeHistogram = s_meter.CreateHistogram<double>(
            name: $"SK.{PlannerType}.CreatePlan.ExecutionTime",
            unit: "ms",
            description: "Tracks the execution time (in milliseconds) of the CreatePlan function.");

    /// <summary>
    /// Counter for the total number of executions of the plan creation.
    /// </summary>
    private static Counter<int> s_executionTotalCounter = s_meter.CreateCounter<int>(
            name: $"SK.{PlannerType}.CreatePlan.ExecutionTotal",
            unit: "Executions",
            description: "Keeps count of the total number of plan creation executions.");

    /// <summary>
    /// Counter for the number of successful executions of the plan creation.
    /// </summary>
    private static Counter<int> s_executionSuccessCounter = s_meter.CreateCounter<int>(
            name: $"SK.{PlannerType}.CreatePlan.ExecutionSuccess",
            unit: "Executions",
            description: "Keeps count of the number of successful plan creation executions.");

    /// <summary>
    /// Counter for the number of failed executions of the plan creation.
    /// </summary>
    private static Counter<int> s_executionFailureCounter = s_meter.CreateCounter<int>(
            name: $"SK.{PlannerType}.CreatePlan.ExecutionFailure",
            unit: "Executions",
            description: "Keeps count of the number of failed plan creation executions.");

    #endregion
}
