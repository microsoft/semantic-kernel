// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.AI;
using Microsoft.SemanticKernel.Orchestration;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using main namespace
namespace Microsoft.SemanticKernel;
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
    /// <param name="resultsSeparator">Separator to use between results.</param>
    /// <param name="settings">Optional request settings.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>Aggregated results.</returns>
    public static async Task<SKContext> AggregatePartitionedResultsAsync(
        this ISKFunction func,
        List<string> partitionedInput,
        SKContext context,
        string resultsSeparator = "\n",
        AIRequestSettings? settings = null,
        CancellationToken cancellationToken = default)
    {
        var results = new List<string>();
        foreach (var partition in partitionedInput)
        {
            context.Variables.Update(partition);
            context = await func.InvokeAsync(context, settings, cancellationToken).ConfigureAwait(false);

            results.Add(context.Variables.ToString());
        }

        context.Variables.Update(string.Join(resultsSeparator, results));
        return context;
    }
}
