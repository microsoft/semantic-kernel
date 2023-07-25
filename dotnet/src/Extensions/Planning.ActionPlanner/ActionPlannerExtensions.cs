// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planning.Action;

/// <summary>
/// Extension methods for <see cref="ActionPlanner"/> class.
/// </summary>
public static class ActionPlannerExtensions
{
    /// <summary>
    /// Returns decorated instance of <see cref="IActionPlanner"/> with enabled instrumentation.
    /// </summary>
    /// <param name="planner">Instance of <see cref="IActionPlanner"/> to decorate.</param>
    /// <param name="logger">Optional logger.</param>
    public static IActionPlanner WithInstrumentation(this IActionPlanner planner, ILogger? logger = null)
    {
        return new InstrumentedActionPlanner(planner, logger);
    }
}
