// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Planning;

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
    /// When using <see cref="Memory"/> to get relevant functions,
    /// this list of functions will be included regardless of relevancy.
    /// </summary>
    public HashSet<(string, string)> IncludedFunctions { get; } = new();

    /// <summary>
    /// Semantic memory to use for function lookup (optional).
    /// This property will be ignored if <see cref="GetAvailableFunctionsAsync"/> is set.
    /// </summary>
    public ISemanticTextMemory Memory { get; set; } = NullMemory.Instance;

    /// <summary>
    /// The maximum number of relevant functions to include in the plan.
    /// </summary>
    /// <remarks>
    /// Limits the number of relevant functions as result of semantic
    /// search included in the plan creation request.
    /// <see cref="IncludedFunctions"/> will be included
    /// in the plan regardless of this limit.
    /// </remarks>
    public int MaxRelevantFunctions { get; set; } = 100;

    /// <summary>
    /// The minimum relevancy score for a function to be considered
    /// </summary>
    /// <remarks>
    /// Depending on the embeddings engine used, the user ask, the step goal
    /// and the functions available, this value may need to be adjusted.
    /// For default, this is set to null to exhibit previous behavior.
    /// </remarks>
    public double? RelevancyThreshold { get; set; }

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
}
