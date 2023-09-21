// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planners.Sequential;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.Orchestration;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="SKContext"/> class to work with sequential planners.
/// </summary>
public static class SKContextSequentialPlannerExtensions
{
    internal const string PlannerMemoryCollectionName = "Planning.SKFunctionsManual";

    internal const string PlanSKFunctionsAreRemembered = "Planning.SKFunctionsAreRemembered";

    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="context">The SKContext to get the functions manual for.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="config">The planner plugin config.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    public static async Task<string> GetFunctionsManualAsync(
        this SKContext context,
        string? semanticQuery = null,
        SequentialPlannerConfig? config = null,
        CancellationToken cancellationToken = default)
    {
        config ??= new SequentialPlannerConfig();

        // Use configured function provider if available, otherwise use the default SKContext function provider.
        IOrderedEnumerable<FunctionView> functions = config.GetAvailableFunctionsAsync is null ?
            await context.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken).ConfigureAwait(false) :
            await config.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken).ConfigureAwait(false);

        return string.Join("\n\n", functions.Select(x => x.ToManualString()));
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded plugins and functions.
    /// </summary>
    /// <param name="context">The SKContext</param>
    /// <param name="config">The planner config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded plugins and functions.</returns>
    public static async Task<IOrderedEnumerable<FunctionView>> GetAvailableFunctionsAsync(
        this SKContext context,
        SequentialPlannerConfig config,
        string? semanticQuery = null,
        CancellationToken cancellationToken = default)
    {
        var functionsView = context.Functions.GetFunctionViews();

        var availableFunctions = functionsView
            .Where(s => !config.ExcludedPlugins.Contains(s.PluginName, StringComparer.OrdinalIgnoreCase)
                && !config.ExcludedFunctions.Contains(s.Name, StringComparer.OrdinalIgnoreCase))
            .ToList();

        List<FunctionView>? result = null;
        if (string.IsNullOrEmpty(semanticQuery) || config.Memory is NullMemory || config.RelevancyThreshold is null)
        {
            // If no semantic query is provided, return all available functions.
            // If a Memory provider has not been registered, return all available functions.
            result = availableFunctions;
        }
        else
        {
            result = new List<FunctionView>();

            // Remember functions in memory so that they can be searched.
            await RememberFunctionsAsync(context, config.Memory, availableFunctions, cancellationToken).ConfigureAwait(false);

            // Search for functions that match the semantic query.
            var memories = config.Memory.SearchAsync(
                PlannerMemoryCollectionName,
                semanticQuery!,
                config.MaxRelevantFunctions,
                config.RelevancyThreshold.Value,
                cancellationToken: cancellationToken);

            // Add functions that were found in the search results.
            result.AddRange(await GetRelevantFunctionsAsync(context, availableFunctions, memories, cancellationToken).ConfigureAwait(false));

            // Add any missing functions that were included but not found in the search results.
            var missingFunctions = config.IncludedFunctions
                .Except(result.Select(x => x.Name))
                .Join(availableFunctions, f => f, af => af.Name, (_, af) => af);

            result.AddRange(missingFunctions);
        }

        return result
            .OrderBy(x => x.PluginName)
            .ThenBy(x => x.Name);
    }

    private static async Task<IEnumerable<FunctionView>> GetRelevantFunctionsAsync(
        SKContext context,
        IEnumerable<FunctionView> availableFunctions,
        IAsyncEnumerable<MemoryQueryResult> memories,
        CancellationToken cancellationToken = default)
    {
        ILogger? logger = null;
        var relevantFunctions = new ConcurrentBag<FunctionView>();
        await foreach (var memoryEntry in memories.WithCancellation(cancellationToken))
        {
            var function = availableFunctions.FirstOrDefault(x => x.ToFullyQualifiedName() == memoryEntry.Metadata.Id);
            if (function != null)
            {
                logger ??= context.LoggerFactory.CreateLogger(typeof(SKContext));
                if (logger.IsEnabled(LogLevel.Debug))
                {
                    logger.LogDebug("Found relevant function. Relevance Score: {0}, Function: {1}", memoryEntry.Relevance, function.ToFullyQualifiedName());
                }

                relevantFunctions.Add(function);
            }
        }

        return relevantFunctions;
    }

    /// <summary>
    /// Saves all available functions to memory.
    /// </summary>
    /// <param name="context">The SKContext to save the functions to.</param>
    /// <param name="memory">The memory provided to store the functions to.</param>
    /// <param name="availableFunctions">The available functions to save.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    internal static async Task RememberFunctionsAsync(
        SKContext context,
        ISemanticTextMemory memory,
        List<FunctionView> availableFunctions,
        CancellationToken cancellationToken = default)
    {
        // Check if the functions have already been saved to memory.
        if (context.Variables.ContainsKey(PlanSKFunctionsAreRemembered))
        {
            return;
        }

        foreach (var function in availableFunctions)
        {
            var functionName = function.ToFullyQualifiedName();
            var key = functionName;
            var description = string.IsNullOrEmpty(function.Description) ? functionName : function.Description;
            var textToEmbed = function.ToEmbeddingString();

            // It'd be nice if there were a saveIfNotExists method on the memory interface
            var memoryEntry = await memory.GetAsync(collection: PlannerMemoryCollectionName, key: key, withEmbedding: false,
                cancellationToken: cancellationToken).ConfigureAwait(false);
            if (memoryEntry == null)
            {
                // TODO It'd be nice if the minRelevanceScore could be a parameter for each item that was saved to memory
                // As folks may want to tune their functions to be more or less relevant.
                // Memory now supports these such strategies.
                await memory.SaveInformationAsync(collection: PlannerMemoryCollectionName, text: textToEmbed, id: key, description: description,
                    additionalMetadata: string.Empty, cancellationToken: cancellationToken).ConfigureAwait(false);
            }
        }

        // Set a flag to indicate that the functions have been saved to memory.
        context.Variables.Set(PlanSKFunctionsAreRemembered, "true");
    }
}
