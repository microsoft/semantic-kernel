// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Planning;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Instrumented planner that creates a Stepwise plan using Mrkl systems.
/// Captures planner-related logs and metrics.
/// </summary>
public class InstrumentedStepwisePlanner : IStepwisePlanner
{
    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedStepwisePlanner"/> class.
    /// </summary>
    /// <param name="planner">Instance of <see cref="IStepwisePlanner"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public InstrumentedStepwisePlanner(
        IStepwisePlanner planner,
        ILoggerFactory? loggerFactory = null)
    {
        this._planner = planner;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(typeof(InstrumentedStepwisePlanner)) : NullLogger.Instance;
    }

    /// <inheritdoc />
    public Plan CreatePlan(string goal)
    {
        using var activity = s_activitySource.StartActivity($"{PlannerType}.CreatePlan");

        this._logger.LogInformation("{PlannerType}: Plan creation started.", PlannerType);

        // Sensitive data, logging as trace, disabled by default
        this._logger.LogTrace("{PlannerType}: Plan Goal: {Goal}", PlannerType, goal);

        var stopwatch = new Stopwatch();

        try
        {
            stopwatch.Start();

            var plan = this._planner.CreatePlan(goal);

            stopwatch.Stop();

            this._logger.LogInformation("{PlannerType}: Plan creation status: {Status}", PlannerType, "Success");

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

    private const string PlannerType = nameof(StepwisePlanner);

    private readonly IStepwisePlanner _planner;
    private readonly ILogger _logger;

    /// <summary>
    /// Instance of <see cref="ActivitySource"/> for planner-related activities.
    /// </summary>
    private static readonly ActivitySource s_activitySource = new(typeof(InstrumentedStepwisePlanner).FullName);

    /// <summary>
    /// Instance of <see cref="Meter"/> for planner-related metrics.
    /// </summary>
    private static readonly Meter s_meter = new(typeof(InstrumentedStepwisePlanner).FullName);

    /// <summary>
    /// Instance of <see cref="Histogram{T}"/> to record plan creation execution time.
    /// </summary>
    private static readonly Histogram<double> s_createPlanExecutionTime =
        s_meter.CreateHistogram<double>(
            name: $"SK.{PlannerType}.CreatePlan.ExecutionTime",
            unit: "ms",
            description: "Execution time of plan creation");

    #endregion
}
