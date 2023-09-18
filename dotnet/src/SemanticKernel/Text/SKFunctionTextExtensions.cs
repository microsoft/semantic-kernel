// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of ISKFunction
namespace Microsoft.SemanticKernel.SkillDefinition;
#pragma warning restore IDE0130

/// <summary>
/// Class with extension methods for semantic functions.
/// </summary>
public static class SKFunctionTextExtensions
{
    /// <summary>
    /// Extension method to aggregate partitioned results of a semantic function.
    /// </summary>
    /// <param name="func">Semantic Kernel function</param>
    /// <param name="partitionedInput">Input to aggregate.</param>
    /// <param name="context">Semantic Kernel context.</param>
    /// <returns>Aggregated results.</returns>
    public static async Task<SKContext> AggregatePartitionedResultsAsync(
        this ISKFunction func,
        List<string> partitionedInput,
        SKContext context)
    {
        var results = new List<string>();
        foreach (var partition in partitionedInput)
        {
            context.Variables.Update(partition);
            var result = await func.InvokeAsync(context).ConfigureAwait(false);

            context = result.Context;

            results.Add(context.Variables.ToString());
        }

        context.Variables.Update(string.Join("\n", results));
        return context;
    }
}
