// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

namespace Microsoft.SemanticKernel.Planning.Stepwise;

/// <summary>
/// Extension methods for <see cref="StepwisePlanner"/> class.
/// </summary>
public static class StepwisePlannerExtensions
{
    /// <summary>
    /// Returns decorated instance of <see cref="IStepwisePlanner"/> with enabled instrumentation.
    /// </summary>
    /// <param name="planner">Instance of <see cref="IStepwisePlanner"/> to decorate.</param>
    /// <param name="logger">Optional logger.</param>
    public static IStepwisePlanner WithInstrumentation(this IStepwisePlanner planner, ILogger? logger = null)
    {
        return new InstrumentedStepwisePlanner(planner, logger);
    }
}
