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
        using var activity = s_activitySource.StartActivity("SequentialPlanner.CreatePlan");

        this._logger.LogInformation("Plan creation started.");

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("Plan Goal: {Goal}", goal);

        var stopwatch = new Stopwatch();

        try
        {
            stopwatch.Start();

            var plan = await this._planner.CreatePlanAsync(goal, cancellationToken).ConfigureAwait(false);

            stopwatch.Stop();

            this._logger.LogInformation("Plan creation status: {Status}", "Success");

            this._logger.LogInformation("Created plan: \n {Plan}", plan.ToSafePlanString());

            // Sensitive data, logging as trace, disabled by default
            this._logger.LogTrace("Created plan with details: \n {Plan}", plan.ToPlanString());

            return plan;
        }
        catch (Exception ex)
        {
            this._logger.LogInformation("Plan creation status: {Status}", "Failed");
            this._logger.LogError(ex, "Plan creation exception details: {Message}", ex.Message);

            throw;
        }
        finally
        {
            this._logger.LogInformation("Plan creation finished in {ExecutionTime}ms.", stopwatch.ElapsedMilliseconds);

            s_createPlanExecutionTime.Record(stopwatch.ElapsedMilliseconds);
        }
    }

    #region private ================================================================================

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
            name: "SK.SequentialPlanner.CreatePlan.ExecutionTime",
            unit: "ms",
            description: "Execution time of plan creation");

    #endregion
}
