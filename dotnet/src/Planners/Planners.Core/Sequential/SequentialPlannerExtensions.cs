// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planners.Sequential;

/// <summary>
/// Extension methods for <see cref="SequentialPlanner"/> class.
/// </summary>
public static class SequentialPlannerExtensions
{
    /// <summary>
    /// Returns decorated instance of <see cref="ISequentialPlanner"/> with enabled instrumentation.
    /// </summary>
    /// <param name="planner">Instance of <see cref="ISequentialPlanner"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public static ISequentialPlanner WithInstrumentation(this ISequentialPlanner planner, ILoggerFactory? loggerFactory = null)
    {
        return new InstrumentedSequentialPlanner(planner, loggerFactory);
    }
}
