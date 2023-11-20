// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Logging;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>Provides extension methods for <see cref="IPlanner"/> instances.</summary>
public static class PlannerExtensions
{
    /// <summary>Gets an <see cref="IPlanner"/> that surrounds the invocation of another planner with logging and metrics.</summary>
    /// <param name="planner">Instance of <see cref="IPlanner"/> to decorate.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no additional logging will be performed.</param>
    public static IPlanner WithInstrumentation(this IPlanner planner, ILoggerFactory? loggerFactory = null)
    {
        Verify.NotNull(planner);
        return planner as InstrumentedPlanner ?? new InstrumentedPlanner(planner, loggerFactory);
    }
}
