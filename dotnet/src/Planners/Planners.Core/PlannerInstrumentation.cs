// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - using planners namespace
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>Surrounds the invocation of a planner with logging and metrics.</summary>
internal static class PlannerInstrumentation
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
    internal static async Task<TPlan> CreatePlanAsync<TPlanner, TPlan>(
        Func<TPlanner, string, CancellationToken, Task<TPlan>> createPlanAsync,
        Func<TPlan, string> planToString,
        TPlanner planner, string goal, ILogger logger, CancellationToken cancellationToken)
        where TPlanner : class
        where TPlan : class
    {
        string plannerName = planner.GetType().FullName;

        using var _ = s_activitySource.StartActivity(plannerName);

        if (logger.IsEnabled(LogLevel.Trace))
        {
            logger.LogTrace("Plan creation started. Goal: {Goal}", goal); // Sensitive data, logging as trace, disabled by default
        }
        else if (logger.IsEnabled(LogLevel.Information))
        {
            logger.LogInformation("Plan creation started.");
        }

        TagList tags = new() { { "sk.planner.name", plannerName } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            var plan = await createPlanAsync(planner, goal, cancellationToken).ConfigureAwait(false);

            if (logger.IsEnabled(LogLevel.Information))
            {
                logger.LogInformation("Plan created. Plan:\n{Plan}", planToString(plan));
            }

            return plan;
        }
        catch (Exception ex)
        {
            logger.LogError(ex, "Plan creation failed. Error: {Message}", ex.Message);
            tags.Add("error.type", ex.GetType().FullName);
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            logger.LogInformation("Plan creation duration: {Duration}ms.", duration.TotalMilliseconds);
            s_createPlanDuration.Record(duration.TotalSeconds, in tags);
        }
    }
}
