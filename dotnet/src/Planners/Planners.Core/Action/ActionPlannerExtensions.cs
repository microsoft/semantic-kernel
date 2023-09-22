// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Extension methods for <see cref="ActionPlanner"/> class.
/// </summary>
public static class ActionPlannerExtensions
{
    /// <summary>
    /// Returns decorated instance of <see cref="IActionPlanner"/> with enabled instrumentation.
    /// </summary>
    /// <param name="planner">Instance of <see cref="IActionPlanner"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public static IActionPlanner WithInstrumentation(this IActionPlanner planner, ILoggerFactory? loggerFactory = null)
    {
        return new InstrumentedActionPlanner(planner, loggerFactory);
    }
}
