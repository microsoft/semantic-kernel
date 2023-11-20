// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Diagnostics;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planning;
#pragma warning restore IDE0130

/// <summary>Represents a planner that creates a plan to achieve a goal.</summary>
public interface IPlanner
{
    /// <summary>Creates a plan for the specified goal.</summary>
    /// <param name="goal">The goal for which a plan should be created.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>The created plan.</returns>
    /// <exception cref="ArgumentNullException"><paramref name="goal"/> is null.</exception>
    /// <exception cref="ArgumentException"><paramref name="goal"/> is empty or entirely composed of whitespace.</exception>
    /// <exception cref="SKException">A plan could not be created.</exception>
    Task<Plan> CreatePlanAsync(string goal, CancellationToken cancellationToken = default);
}
