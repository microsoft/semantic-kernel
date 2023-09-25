// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Base class for planner configs
/// </summary>
public abstract class PlannerConfigBase
{
    /// <summary>
    /// Delegate to get the prompt template string.
    /// </summary>
    public Func<string>? GetPromptTemplate { get; set; } = null;

    /// <summary>
    /// A list of plugins to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedPlugins { get; } = new();

    /// <summary>
    /// A list of functions to exclude from the plan creation request.
    /// </summary>
    public HashSet<string> ExcludedFunctions { get; } = new();

    /// <summary>
    /// Semantic Memory configuration, used to enable function filtering during plan creation.
    /// </summary>
    /// <remarks>
    /// This configuration will be ignored if <see cref="GetAvailableFunctionsAsync"/> is set.
    /// </remarks>
    public SemanticMemoryConfig SemanticMemoryConfig { get; set; } = new();

    /// <summary>
    /// Callback to get the available functions for planning (optional).
    /// Use if you want to override the default function lookup behavior.
    /// If set, this function takes precedence over <see cref="Memory"/>.
    /// Setting <see cref="ExcludedPlugins"/>, <see cref="ExcludedFunctions"/> will be used to filter the results.
    /// </summary>
    public Func<PlannerConfigBase, string?, CancellationToken, Task<IOrderedEnumerable<FunctionView>>>? GetAvailableFunctionsAsync { get; set; }

    /// <summary>
    /// Callback to get a function by name (optional).
    /// Use if you want to override the default function lookup behavior.
    /// </summary>
    public Func<string, string, ISKFunction?>? GetFunctionCallback { get; set; }

    /// <summary>
    /// The maximum total number of tokens to allow in a completion request,
    /// which includes the tokens from the prompt and completion
    /// </summary>
    public int MaxTokens { get; set; }
}
