// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Text.Json;
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
        name: "semantic_kernel.planning.create_plan.duration",
        unit: "s",
        description: "Duration time of plan creation.");

    /// <summary><see cref="Histogram{T}"/> to record plan execution duration.</summary>
    private static readonly Histogram<double> s_planExecutionDuration = s_meter.CreateHistogram<double>(
        name: "semantic_kernel.planning.invoke_plan.duration",
        unit: "s",
        description: "Duration time of plan execution.");

    /// <summary>Invokes the supplied <paramref name="createPlanAsync"/> delegate, surrounded by logging and metrics.</summary>
    public static async Task<TPlan> CreatePlanAsync<TPlanner, TPlan>(
        Func<TPlanner, Kernel, string, KernelArguments?, CancellationToken, Task<TPlan>> createPlanAsync,
        TPlanner planner, Kernel kernel, string goal, KernelArguments? arguments, ILogger logger, CancellationToken cancellationToken)
        where TPlanner : class
        where TPlan : class
    {
        string plannerName = planner.GetType().FullName;

        using var activity = s_activitySource.StartActivity(plannerName);

        logger.LogCreatePlanStarted();
        logger.LogGoal(goal);

        TagList tags = new() { { "semantic_kernel.planner.name", plannerName } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            var plan = await createPlanAsync(planner, kernel, goal, arguments, cancellationToken).ConfigureAwait(false);
            logger.LogPlanCreated();
            logger.LogPlan(plan);

            return plan;
        }
        catch (Exception ex)
        {
            tags.Add("error.type", ex.GetType().FullName);
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            logger.LogCreatePlanError(ex, ex.Message);
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            logger.LogCreatePlanDuration(duration.TotalSeconds);
            s_createPlanDuration.Record(duration.TotalSeconds, in tags);
        }
    }

    // <summary>Invokes the supplied <paramref name="InvokePlanAsync"/> delegate, surrounded by logging and metrics.</summary>
    public static async Task<TPlanResult> InvokePlanAsync<TPlan, TPlanInput, TPlanResult>(
        Func<TPlan, Kernel, TPlanInput?, CancellationToken, Task<TPlanResult>> InvokePlanAsync,
        TPlan plan, Kernel kernel, TPlanInput? input, ILogger logger, CancellationToken cancellationToken)
        where TPlan : class
        where TPlanInput : class
        where TPlanResult : class
    {
        string planName = plan.GetType().FullName;
        using var activity = s_activitySource.StartActivity(planName);

        logger.LogInvokePlanStarted();

        TagList tags = new() { { "semantic_kernel.plan.name", planName } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            TPlanResult planResult = await InvokePlanAsync(plan, kernel, input, cancellationToken).ConfigureAwait(false);

            logger.LogInvokePlanSuccess();
            logger.LogPlanResult(planResult);

            return planResult;
        }
        catch (Exception ex)
        {
            tags.Add("error.type", ex.GetType().FullName);
            activity?.SetStatus(ActivityStatusCode.Error, ex.Message);
            logger.LogInvokePlanError(ex, ex.Message);
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            logger.LogInvokePlanDuration(duration.TotalSeconds);
            s_planExecutionDuration.Record(duration.TotalSeconds, in tags);
        }
    }

    #region CreatePlan Logging helpers
#pragma warning disable SYSLIB1006 // Multiple logging methods cannot use the same event id within a class
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan creation started.")]
    static partial void LogCreatePlanStarted(this ILogger logger);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Trace, // Sensitive data, logging as trace, disabled by default
        Message = "Goal: {Goal}")]
    static partial void LogGoal(this ILogger logger, string goal);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan created.")]
    static partial void LogPlanCreated(this ILogger logger);

    private static readonly Action<ILogger, string, Exception?> s_logPlan =
        LoggerMessage.Define<string>(
            logLevel: LogLevel.Trace,   // Sensitive data, logging as trace, disabled by default
            eventId: 0,
            "Plan:\n{Plan}");
    private static void LogPlan(this ILogger logger, object plan)
    {
        if (logger.IsEnabled(LogLevel.Trace))
        {
            try
            {
                var jsonString = JsonSerializer.Serialize(plan);
                s_logPlan(logger, jsonString, null);
            }
            catch (NotSupportedException ex)
            {
                s_logPlan(logger, "Failed to serialize plan to Json", ex);
            }
        }
    }

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "Plan creation failed. Error: {Message}")]
    static partial void LogCreatePlanError(this ILogger logger, Exception exception, string message);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan creation duration: {Duration}s.")]
    static partial void LogCreatePlanDuration(this ILogger logger, double duration);

    #endregion

    #region InvokePlan Logging helpers
    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan execution started.")]
    static partial void LogInvokePlanStarted(this ILogger logger);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan executed successfully.")]
    static partial void LogInvokePlanSuccess(this ILogger logger);

    private static readonly Action<ILogger, string, Exception?> s_logPlanResult =
        LoggerMessage.Define<string>(
            logLevel: LogLevel.Trace,   // Sensitive data, logging as trace, disabled by default
            eventId: 0,
            "Plan result: {Result}");

    private static void LogPlanResult(this ILogger logger, object planResult)
    {
        if (logger.IsEnabled(LogLevel.Trace))
        {
            try
            {
                var jsonString = planResult.GetType() == typeof(string)
                    ? planResult.ToString()
                    : JsonSerializer.Serialize(planResult);
                s_logPlanResult(logger, jsonString, null);
            }
            catch (NotSupportedException ex)
            {
                s_logPlanResult(logger, "Failed to serialize plan result to Json", ex);
            }
        }
    }

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Error,
        Message = "Plan execution failed. Error: {Message}")]
    static partial void LogInvokePlanError(this ILogger logger, Exception exception, string message);

    [LoggerMessage(
        EventId = 0,
        Level = LogLevel.Information,
        Message = "Plan execution duration: {Duration}s.")]
    static partial void LogInvokePlanDuration(this ILogger logger, double duration);

#pragma warning restore SYSLIB1006 // Multiple logging methods cannot use the same event id within a class
    #endregion
}
