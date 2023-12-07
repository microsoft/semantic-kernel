// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>Surrounds the invocation of a planner with logging and metrics.</summary>
internal static partial class PlannerInstrumentation
{
    /// <summary><see cref="ActivitySource"/> for planning-related activities.</summary>
    private static readonly ActivitySource s_activitySource = new("Microsoft.SemanticKernel.Planning");

    /// <summary><see cref="Meter"/> for planner-related metrics.</summary>
    private static readonly Meter s_meter = new("Microsoft.SemanticKernel.Planning");

    /// <summary><see cref="Histogram{T}"/> to record plan creation duration.</summary>
    private static readonly Histogram<double> s_createPlanDuration = s_meter.CreateHistogram<double>(
        name: "sk.planning.create_plan.duration",
        unit: "s",
        description: "Duration time of plan creation.");

    /// <summary>Invokes the supplied <paramref name="createPlanAsync"/> delegate, surrounded by logging and metrics.</summary>
    public static async Task<TPlan> CreatePlanAsync<TPlanner, TPlan>(
        Func<TPlanner, Kernel, string, CancellationToken, Task<TPlan>> createPlanAsync,
        TPlanner planner, Kernel kernel, string goal, ILogger logger, CancellationToken cancellationToken)
        where TPlanner : class
        where TPlan : class
    {
        string plannerName = planner.GetType().FullName;

        using var _ = s_activitySource.StartActivity(plannerName);

        logger.LogPlanCreationStarted();
        logger.LogGoal(goal);

        TagList tags = new() { { "sk.planner.name", plannerName } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            var plan = await createPlanAsync(planner, kernel, goal, cancellationToken).ConfigureAwait(false);
            logger.LogPlanCreated();
            logger.LogPlan(plan);

            return plan;
        }
        catch (Exception ex)
        {
            logger.LogPlanCreationError(ex, ex.Message);
            tags.Add("error.type", ex.GetType().FullName);
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            logger.LogPlanCreationDuration(duration.TotalSeconds);
            s_createPlanDuration.Record(duration.TotalSeconds, in tags);
        }
    }

    #region Logging helpers
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan creation started.")]
    static partial void LogPlanCreationStarted(this ILogger logger);

    [LoggerMessage(
        EventId = 1,
        Level = LogLevel.Trace, // Sensitive data, logging as trace, disabled by default
        Message = "Goal: {Goal}")]
    static partial void LogGoal(this ILogger logger, string goal);

    [LoggerMessage(
        EventId = 2,
        Level = LogLevel.Information,
        Message = "Plan created.")]
    static partial void LogPlanCreated(this ILogger logger);

    [LoggerMessage(
        EventId = 3,
        Level = LogLevel.Trace, // Sensitive data, logging as trace, disabled by default
        Message = "Plan:\n{Plan}")]
    static partial void LogPlan(this ILogger logger, object plan);

    [LoggerMessage(
        EventId = 4,
        Level = LogLevel.Error,
        Message = "Plan creation failed. Error: {Message}")]
    static partial void LogPlanCreationError(this ILogger logger, Exception exception, string message);

    [LoggerMessage(
        EventId = 5,
        Level = LogLevel.Information,
        Message = "Plan creation duration: {Duration}s.")]
    static partial void LogPlanCreationDuration(this ILogger logger, double duration);

    #endregion
}
