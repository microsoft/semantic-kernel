// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

namespace Microsoft.SemanticKernel.Planners.Handlebars;

/// <summary>
/// Interface for planner that uses a set of semantic functions to create a sequential plan.
/// </summary>
public interface IHandlebarsPlanner
{
    /// <summary>
    /// Gets the stopwatch used for measuring planning time.
    /// </summary>
    Stopwatch Stopwatch { get; }

    /// <summary>
    /// Create a plan for a goal.
    /// </summary>
    /// <param name="goal">The goal to create a plan for.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The plan.</returns>
    /// <exception cref="SKException">Thrown when the plan cannot be created.</exception>
    Task<HandlebarsPlan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default);
}
