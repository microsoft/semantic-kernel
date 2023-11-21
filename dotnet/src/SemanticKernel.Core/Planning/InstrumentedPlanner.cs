// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics;
using System.Diagnostics.Metrics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - using planners namespace
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>Instrumented planner that surrounds the invocation of another planner with logging and metrics.</summary>
internal sealed class InstrumentedPlanner : IPlanner
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

    /// <summary>Wrapped planner instance.</summary>
    private readonly IPlanner _planner;

    /// <summary>Logger to use for logging activities.</summary>
    private readonly ILogger _logger;

    /// <summary>Creates a new instance of the <see cref="InstrumentedPlanner"/> class.</summary>
    /// <param name="planner">Instance of <see cref="IPlanner"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public InstrumentedPlanner(IPlanner planner, ILoggerFactory? loggerFactory = null)
    {
        this._planner = planner;
        this._logger = loggerFactory is not null ? loggerFactory.CreateLogger(planner.GetType()) : NullLogger.Instance;
    }

    /// <inheritdoc />
    async Task<Plan> IPlanner.CreatePlanAsync(string goal, CancellationToken cancellationToken)
    {
        string plannerName = this._planner.GetType().FullName;

        using var _ = s_activitySource.StartActivity(plannerName);

        if (this._logger.IsEnabled(LogLevel.Trace))
        {
            this._logger.LogTrace("Plan creation started. Goal: {Goal}", goal); // Sensitive data, logging as trace, disabled by default
        }
        else if (this._logger.IsEnabled(LogLevel.Information))
        {
            this._logger.LogInformation("Plan creation started.");
        }

        TagList tags = new() { { "sk.planner.name", plannerName } };
        long startingTimestamp = Stopwatch.GetTimestamp();
        try
        {
            var plan = await this._planner.CreatePlanAsync(goal, cancellationToken).ConfigureAwait(false);

            if (this._logger.IsEnabled(LogLevel.Trace))
            {
                this._logger.LogTrace("Plan created:\n{Plan}", plan.ToPlanString()); // Sensitive data, logging as trace, disabled by default
            }
            else if (this._logger.IsEnabled(LogLevel.Information))
            {
                this._logger.LogInformation("Plan created:\n{Plan}", plan.ToSafePlanString());
            }

            return plan;
        }
        catch (Exception ex)
        {
            this._logger.LogError(ex, "Plan creation failed: {Message}", ex.Message);
            tags.Add("error.type", ex.GetType().FullName);
            throw;
        }
        finally
        {
            TimeSpan duration = new((long)((Stopwatch.GetTimestamp() - startingTimestamp) * (10_000_000.0 / Stopwatch.Frequency)));
            this._logger.LogInformation("Plan creation duration: {Duration}ms.", duration.TotalMilliseconds);
            s_createPlanDuration.Record(duration.TotalSeconds, in tags);
        }
    }
}
