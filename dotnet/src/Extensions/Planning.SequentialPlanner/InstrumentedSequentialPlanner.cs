// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
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
    public async Task<Plan> CreatePlanAsync(string goal)
    {
        using var activity = s_activitySource.StartActivity($"{PlannerType}.CreatePlan");

        this._logger.LogInformation("{PlannerType}: Plan creation started.", PlannerType);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("{PlannerType}: Plan Goal: {Goal}", PlannerType, goal);

        var stopwatch = new Stopwatch();

        try
        {
            stopwatch.Start();

            var plan = await this._planner.CreatePlanAsync(goal).ConfigureAwait(false);

            stopwatch.Stop();

            this._logger.LogInformation("{PlannerType}: Plan creation status: {Status}", PlannerType, "Success");

            this._logger.LogInformation("{PlannerType}: Created plan: \n {Plan}", PlannerType, plan.ToSafePlanString());

            // Sensitive data, logging as trace, disabled by default
            this._logger.LogTrace("{PlannerType}: Created plan with details: \n {Plan}", PlannerType, plan.ToPlanString());

            return plan;
        }
        catch (Exception ex)
        {
            this._logger.LogInformation("{PlannerType}: Plan creation status: {Status}", PlannerType, "Failed");
            this._logger.LogError(ex, "{PlannerType}: Plan creation exception details: {Message}", PlannerType, ex.Message);

            throw;
        }
        finally
        {
            this._logger.LogInformation("{PlannerType}: Plan creation finished in {ExecutionTime}ms.", PlannerType, stopwatch.ElapsedMilliseconds);

            s_createPlanExecutionTime.Record(stopwatch.ElapsedMilliseconds);
        }
    }

    #region private ================================================================================

    private const string PlannerType = nameof(SequentialPlanner);

    private readonly ISequentialPlanner _planner;
    private readonly ILogger _logger;

    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for planner-related activities.
    /// </summary>
    private static ActivitySource s_activitySource = new(typeof(InstrumentedSequentialPlanner).FullName);

    /// <summary>
    /// Instance of <see cref="Meter"/> for planner-related metrics.
    /// </summary>
    private static Meter s_meter = new(typeof(InstrumentedSequentialPlanner).FullName);

    /// <summary>
    /// Instance of <see cref="Histogram{T}"/> to record plan creation execution time.
    /// </summary>
    private static Histogram<double> s_createPlanExecutionTime =
        s_meter.CreateHistogram<double>(
            name: $"SK.{PlannerType}.CreatePlan.ExecutionTime",
            unit: "ms",
            description: "Execution time of plan creation");

    #endregion
}
