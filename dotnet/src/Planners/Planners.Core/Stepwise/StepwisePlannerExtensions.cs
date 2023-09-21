// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planners.Stepwise;

/// <summary>
/// Extension methods for <see cref="StepwisePlanner"/> class.
/// </summary>
public static class StepwisePlannerExtensions
{
    /// <summary>
    /// Returns decorated instance of <see cref="IStepwisePlanner"/> with enabled instrumentation.
    /// </summary>
    /// <param name="planner">Instance of <see cref="IStepwisePlanner"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    public static IStepwisePlanner WithInstrumentation(this IStepwisePlanner planner, ILoggerFactory? loggerFactory = null)
    {
        return new InstrumentedStepwisePlanner(planner, loggerFactory);
    }
}
