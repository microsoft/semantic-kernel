// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Planner config with semantic memory
/// </summary>
public abstract class PlannerOptions
{
    /// <summary>
    /// A list of plugins to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedPlugins { get; } = new();

    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; } = new();

    /// <summary>
    /// Callback to get the available functions for planning (optional).
    /// Use if you want to override the default function lookup behavior.
    /// If set, this function takes precedence over <see cref="Memory"/>.
    /// Setting <see cref="ExcludedPlugins"/>, <see cref="ExcludedFunctions"/> will be used to filter the results.
    /// </summary>
    public Func<PlannerOptions, string?, CancellationToken, Task<IEnumerable<KernelFunctionMetadata>>>? GetAvailableFunctionsAsync { get; set; }

    /// <summary>
    /// Semantic Memory configuration, used to enable function filtering during plan creation.
    /// </summary>
    /// <remarks>
    /// This configuration will be ignored if GetAvailableFunctionsAsync is set.
    /// </remarks>
    public SemanticMemoryConfig SemanticMemoryConfig { get; set; } = new();
}
