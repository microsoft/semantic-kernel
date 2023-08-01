// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Extension methods for <see cref="SequentialPlanner"/> class.
/// </summary>
public static class SequentialPlannerExtensions
{
    /// <summary>
    /// Returns decorated instance of <see cref="ISequentialPlanner"/> with enabled instrumentation.
    /// </summary>
    /// <param name="planner">Instance of <see cref="ISequentialPlanner"/> to decorate.</param>
    /// <param name="logger">Optional logger.</param>
    public static ISequentialPlanner WithInstrumentation(this ISequentialPlanner planner, ILogger? logger = null)
    {
        return new InstrumentedSequentialPlanner(planner, logger);
    }
}
