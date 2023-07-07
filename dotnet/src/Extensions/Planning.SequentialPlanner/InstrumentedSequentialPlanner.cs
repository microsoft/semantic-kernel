// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics.Metering;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Instrumented planner that uses semantic function to create a sequential plan.
/// Captures planner-related logs and metrics.
/// </summary>
public sealed class InstrumentedSequentialPlanner : ISequentialPlanner
{
    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for planner-related activities.
    /// </summary>
    private static ActivitySource activitySource = new(typeof(InstrumentedSequentialPlanner).FullName);

    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedSequentialPlanner"/> class.
    /// </summary>
    /// <param name="planner">Instance of <see cref="ISequentialPlanner"/> to decorate.</param>
    /// <param name="logger">Optional logger.</param>
    /// <param name="meter">Optional meter.</param>
    public InstrumentedSequentialPlanner(
        ISequentialPlanner planner,
        ILogger? logger = null,
        IMeter? meter = null)
    {
        this._planner = planner;
        this._logger = logger ?? NullLogger.Instance;
        this._meter = meter ?? NullMeter.Instance;
    }

    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal)
    {
        using var activity = activitySource.StartActivity("SequentialPlanner.CreatePlan");

        this._logger.LogInformation("Plan creation started.");
        this._logger.LogTrace("Plan Goal: {Goal}", goal);

        var stopwatch = new Stopwatch();

        try
        {
            stopwatch.Start();

            var plan = await this._planner.CreatePlanAsync(goal).ConfigureAwait(false);

            stopwatch.Stop();

            this._logger.LogInformation("Plan creation status: {Status}", "Success");

            this._logger.LogInformation("Created plan: \n {Plan}", plan.ToSafePlanString());
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

            this._meter.TrackMetric(CreatePlanExecutionTimeMetricName, stopwatch.ElapsedMilliseconds);
        }
    }

    #region private ================================================================================

    private const string CreatePlanExecutionTimeMetricName = "SK.SequentialPlanner.CreatePlan.ExecutionTime";

    private readonly ISequentialPlanner _planner;
    private readonly ILogger _logger;
    private readonly IMeter _meter;

    #endregion
}
