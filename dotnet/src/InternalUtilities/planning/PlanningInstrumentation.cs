// Copyright (c) Microsoft. All rights reserved.

using System.Diagnostics;
using System.Diagnostics.Metrics;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Instrumentation source for planning-related modules.
/// </summary>
internal static class PlanningInstrumentation
{
    /// <summary><see cref="ActivitySource"/> for planning-related activities.</summary>
    public static readonly ActivitySource ActivitySource = new("Microsoft.SemanticKernel.Planning");

    /// <summary><see cref="Meter"/> for planner-related metrics.</summary>
    public static readonly Meter Meter = new("Microsoft.SemanticKernel.Planning");
}
