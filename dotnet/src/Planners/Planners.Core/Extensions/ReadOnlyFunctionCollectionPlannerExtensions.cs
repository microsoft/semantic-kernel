// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning;

#pragma warning disable IDE0130
namespace Microsoft.SemanticKernel.Planners;
#pragma warning restore IDE0130

/// <summary>
/// Provides extension methods for the <see cref="IReadOnlyFunctionCollection"/> implementations for planners.
/// </summary>
public static class ReadOnlyFunctionCollectionPlannerExtensions
{
    internal const string PlannerMemoryCollectionName = "Planning.SKFunctionsManual";

    /// <summary>
    /// Returns a function callback that can be used to retrieve a function from the function provider.
    /// </summary>
    /// <param name="functions">The function provider.</param>
    /// <returns>A function callback that can be used to retrieve a function from the function provider.</returns>
    public static Func<string, string, ISKFunction?> GetFunctionCallback(this IReadOnlyFunctionCollection functions)
    {
        return (pluginName, functionName) =>
        {
            if (string.IsNullOrEmpty(pluginName))
            {
                if (functions.TryGetFunction(functionName, out var pluginFunction))
                {
                    return pluginFunction;
                }
            }
            else if (functions.TryGetFunction(pluginName, functionName, out var pluginFunction))
            {
                return pluginFunction;
            }

            return null;
        };
    }

    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="functions">The function provider.</param>
    /// <param name="config">The planner config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="logger">The logger to use for logging.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    public static async Task<string> GetFunctionsManualAsync(
        this IReadOnlyFunctionCollection functions,
        PlannerConfigBase config,
        string? semanticQuery = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        IOrderedEnumerable<FunctionView> availableFunctions = await functions.GetFunctionsAsync(config, semanticQuery, logger, cancellationToken).ConfigureAwait(false);

        return string.Join("\n\n", availableFunctions.Select(x => x.ToManualString()));
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded plugins and functions.
    /// </summary>
    /// <param name="functions">The function provider.</param>
    /// <param name="config">The planner config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="logger">The logger to use for logging.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded plugins and functions.</returns>
    public static async Task<IOrderedEnumerable<FunctionView>> GetFunctionsAsync(this IReadOnlyFunctionCollection functions, PlannerConfigBase config, string? semanticQuery, ILogger? logger, CancellationToken cancellationToken)
    {
        // Use configured function provider if available, otherwise use the default SKContext function provider.
        return config.GetAvailableFunctionsAsync is null ?
            await functions.GetAvailableFunctionsAsync(config, semanticQuery, logger, cancellationToken).ConfigureAwait(false) :
            await config.GetAvailableFunctionsAsync(config, semanticQuery, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded plugins and functions.
    /// </summary>
    /// <param name="functions">The function provider.</param>
    /// <param name="config">The planner config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="logger">The logger to use for logging.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded plugins and functions.</returns>
    public static async Task<IOrderedEnumerable<FunctionView>> GetAvailableFunctionsAsync(
        this IReadOnlyFunctionCollection functions,
        PlannerConfigBase config,
        string? semanticQuery = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        var functionsView = functions.GetFunctionViews();

        var availableFunctions = functionsView
            .Where(s => !config.ExcludedPlugins.Contains(s.PluginName, StringComparer.OrdinalIgnoreCase)
                && !config.ExcludedFunctions.Contains(s.Name, StringComparer.OrdinalIgnoreCase))
            .ToList();

        List<FunctionView>? result = null;
        var semanticMemoryConfig = config.SemanticMemory;
        if (string.IsNullOrEmpty(semanticQuery) || semanticMemoryConfig.Memory is NullMemory)
        {
            // If no semantic query is provided, return all available functions.
            // If a Memory provider has not been registered, return all available functions.
            result = availableFunctions;
        }
        else
        {
            result = new List<FunctionView>();

            // Remember functions in memory so that they can be searched.
            await RememberFunctionsAsync(semanticMemoryConfig.Memory, availableFunctions, cancellationToken).ConfigureAwait(false);

            // Search for functions that match the semantic query.
            var memories = semanticMemoryConfig.Memory.SearchAsync(
                PlannerMemoryCollectionName,
                semanticQuery!,
                semanticMemoryConfig.MaxRelevantFunctions,
                semanticMemoryConfig.RelevancyThreshold.HasValue ? semanticMemoryConfig.RelevancyThreshold.Value : 0.0,
cancellationToken: cancellationToken);

            // Add functions that were found in the search results.
            result.AddRange(await GetRelevantFunctionsAsync(availableFunctions, memories, logger, cancellationToken).ConfigureAwait(false));

            // Add any missing functions that were included but not found in the search results.
            var missingFunctions = semanticMemoryConfig.IncludedFunctions
                .Except(result.Select(x => (x.PluginName, x.Name)))
                .Join(availableFunctions, f => f, af => (af.PluginName, af.Name), (_, af) => af);

            result.AddRange(missingFunctions);
        }

        return result
            .OrderBy(x => x.PluginName)
            .ThenBy(x => x.Name);
    }

    private static async Task<IEnumerable<FunctionView>> GetRelevantFunctionsAsync(
        IEnumerable<FunctionView> availableFunctions,
        IAsyncEnumerable<MemoryQueryResult> memories,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        var relevantFunctions = new ConcurrentBag<FunctionView>();
        await foreach (var memoryEntry in memories.WithCancellation(cancellationToken))
        {
            var function = availableFunctions.FirstOrDefault(x => x.ToFullyQualifiedName() == memoryEntry.Metadata.Id);
            if (function != null)
            {
                if (logger is not null && logger.IsEnabled(LogLevel.Debug))
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
    /// <param name="memory">The memory provided to store the functions to.</param>
    /// <param name="availableFunctions">The available functions to save.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private static async Task RememberFunctionsAsync(
        ISemanticTextMemory memory,
        List<FunctionView> availableFunctions,
        CancellationToken cancellationToken = default)
    {
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
    }
}
