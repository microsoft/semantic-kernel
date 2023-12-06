// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>Surrounds the invocation of a planner with logging and metrics.</summary>
internal static partial class PlanInstrumentation
{
    /// <summary><see cref="Histogram{T}"/> to record plan execution duration.</summary>
    private static readonly Histogram<double> s_planExecutionDuration =
        PlanningInstrumentation.Meter.CreateHistogram<double>(
            name: "sk.planning.run_plan.duration",
            unit: "s",
            description: "Duration time of plan execution.");

    /// <summary><see cref="Counter{T}"/> to record planner execution success counts.</summary>
    private static readonly Counter<int> s_executionSuccess =
        PlanningInstrumentation.Meter.CreateCounter<int>(
            name: "sk.planning.run_plan.success",
            unit: "{invocation}",
            description: "Measures the number of successful plan executions");

    /// <summary><see cref="Counter{T}"/> to record planner execution failure counts.</summary>
    private static readonly Counter<int> s_executionFailure =
        PlanningInstrumentation.Meter.CreateCounter<int>(
            name: "sk.planning.run_plan.failure",
            unit: "{invocation}",
            description: "Measures the number of failed plan executions");

    // <summary>Invokes the supplied <paramref name="InvokePlanAsync"/> delegate, surrounded by logging and metrics.</summary>
    public static async Task<TPlanResult> InvokePlanAsync<TPlan, TPlanInput, TPlanResult>(
        Func<TPlan, Kernel, TPlanInput, CancellationToken, Task<TPlanResult>> InvokePlanAsync,
        TPlan plan, Kernel kernel, TPlanInput input, ILogger logger, CancellationToken cancellationToken)
        where TPlan : class
        where TPlanInput : class
        where TPlanResult : class
    {
        string planName = plan.GetType().FullName;
        using var _ = PlanningInstrumentation.ActivitySource.StartActivity(planName);

        logger.LogPlanExecutionStarted();

        TagList tags = new() { { "sk.plan.name", planName } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            TPlanResult planResult = await InvokePlanAsync(plan, kernel, input, cancellationToken).ConfigureAwait(false);

            s_executionSuccess.Add(1, in tags);
            logger.LogPlanExecutionSuccess();
            logger.LogPlanResult(planResult);

            return planResult;
        }
        catch (Exception ex)
        {
            tags.Add("error.type", ex.GetType().FullName);
            s_executionFailure.Add(1, in tags);
            logger.LogPlanExecutionError(ex, ex.Message);
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            logger.LogPlanExecutionDuration(duration.TotalSeconds);
            s_planExecutionDuration.Record(duration.TotalSeconds, in tags);
        }
    }

    #region Logging helpers
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan execution started.")]
    static partial void LogPlanExecutionStarted(this ILogger logger);

    [LoggerMessage(
        EventId = 1,
        Level = LogLevel.Information,
        Message = "Plan executed successfully.")]
    static partial void LogPlanExecutionSuccess(this ILogger logger);

    [LoggerMessage(
        EventId = 2,
        Level = LogLevel.Trace, // Sensitive data, logging as trace, disabled by default
        Message = "Plan result: {PlanResult}")]
    static partial void LogPlanResult(this ILogger logger, object planResult);

    [LoggerMessage(
        EventId = 3,
        Level = LogLevel.Error,
        Message = "Plan creation failed. Error: {Message}")]
    static partial void LogPlanExecutionError(this ILogger logger, Exception exception, string message);

    [LoggerMessage(
        EventId = 4,
        Level = LogLevel.Information,
        Message = "Plan creation duration: {Duration}s.")]
    static partial void LogPlanExecutionDuration(this ILogger logger, double duration);

    #endregion
}
