// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
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
    public InstrumentedSequentialPlanner(ISequentialPlanner planner, ILogger? logger = null)
    {
        this._planner = planner;
        this._logger = logger ?? NullLogger.Instance;
    }

    /// <inheritdoc />
    public async Task<Plan> CreatePlanAsync(string goal)
    {
        this._logger.LogInformation("Plan creation started.");

        this._logger.LogTrace("Plan Goal: {Goal}", goal);

        var stopwatch = Stopwatch.StartNew();

        var plan = await this._planner.CreatePlanAsync(goal).ConfigureAwait(false);

        stopwatch.Stop();

        this._logger.LogTrace("Created plan: \n {Plan}", plan.ToPlanString());

        this._logger.LogInformation("Plan creation finished in {ElapsedMilliseconds}ms.", stopwatch.ElapsedMilliseconds);

        return plan;
    }

    #region private ================================================================================

    private readonly ISequentialPlanner _planner;
    private readonly ILogger _logger;

    #endregion
}
