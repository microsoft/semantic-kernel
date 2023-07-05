// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics.Metering;

namespace Microsoft.SemanticKernel.Planning.Sequential;

/// <summary>
/// Factory to create instance of <see cref="ISequentialPlanner"/>.
/// </summary>
public static class SequentialPlannerFactory
{
    /// <summary>
    /// Initialize a new instance of the <see cref="SequentialPlanner"/> class.
    /// </summary>
    /// <param name="kernel">The semantic kernel instance.</param>
    /// <param name="config">The planner configuration.</param>
    /// <param name="prompt">Optional prompt override.</param>
    /// <returns>Instance of <see cref="ISequentialPlanner"/>.</returns>
    public static ISequentialPlanner GetPlanner(
        IKernel kernel,
        SequentialPlannerConfig? config = null,
        string? prompt = null)
    {
        return new SequentialPlanner(kernel, config, prompt);
    }

    /// <summary>
    /// Initialize a new instance of the <see cref="InstrumentedSequentialPlanner"/> class.
    /// </summary>
    /// <param name="planner">Instance of <see cref="ISequentialPlanner"/> to decorate.</param>
    /// <param name="logger">Optional logger.</param>
    /// <param name="meter">Optional meter.</param>
    /// <returns>Instance of <see cref="ISequentialPlanner"/>.</returns>
    public static ISequentialPlanner WithInstrumentation(
        this ISequentialPlanner planner,
        ILogger? logger = null,
        IMeter? meter = null)
    {
        return new InstrumentedSequentialPlanner(planner, logger, meter);
    }
}
