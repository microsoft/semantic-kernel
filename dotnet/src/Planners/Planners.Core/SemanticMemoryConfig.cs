// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using Microsoft.SemanticKernel.Memory;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of Plan
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Semantic memory configuration.
/// </summary>
public class SemanticMemoryConfig
{
    /// <summary>
    /// A list of functions to be included regardless of relevancy.
    /// </summary>
    public HashSet<(string PluginName, string FunctionName)> IncludedFunctions { get; } = new();

    /// <summary>
    /// Semantic memory to use for filtering function lookup during plan creation.
    /// </summary>
    public ISemanticTextMemory Memory { get; set; } = NullMemory.Instance;

    /// <summary>
    /// The maximum number of relevant functions to search for.
    /// </summary>
    /// <remarks>
    /// Limits the number of relevant functions as result of semantic
    /// search included in the plan creation request.
    /// <see cref="IncludedFunctions"/> will be included
    /// in the plan regardless of this limit.
    /// </remarks>
    public int MaxRelevantFunctions { get; set; } = 100;

    /// <summary>
    /// The minimum relevancy score for a function to be considered.
    /// </summary>
    /// <remarks>
    /// Depending on the embeddings engine used, the user ask, the step goal
    /// and the functions available, this value may need to be adjusted.
    /// For default, this is set to null which will return the top
    /// <see cref="MaxRelevantFunctions"/> sorted by relevancy.
    /// </remarks>
    public double? RelevancyThreshold { get; set; }
}
