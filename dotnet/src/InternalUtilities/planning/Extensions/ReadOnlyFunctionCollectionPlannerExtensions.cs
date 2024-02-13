// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Json.Schema;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Planning;

/// <summary>
/// Provides extension methods for the <see cref="IReadOnlyKernelPluginCollection"/> implementations for planners.
/// </summary>
internal static class ReadOnlyPluginCollectionPlannerExtensions
{
    internal const string PlannerMemoryCollectionName = "Planning.KernelFunctionsManual";

    /// <summary>
    /// Returns a function callback that can be used to retrieve a function from the function provider.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <returns>A function callback that can be used to retrieve a function from the function provider.</returns>
    internal static Func<string, string, KernelFunction?> GetFunctionCallback(this IReadOnlyKernelPluginCollection plugins)
    {
        return (pluginName, functionName) =>
        {
            plugins.TryGetFunction(pluginName, functionName, out var pluginFunction);
            return pluginFunction;
        };
    }

    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="plannerOptions">The planner options.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="logger">The logger to use for logging.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    internal static async Task<string> GetFunctionsManualAsync(
        this IReadOnlyKernelPluginCollection plugins,
        PlannerOptions plannerOptions,
        string? semanticQuery = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        IEnumerable<KernelFunctionMetadata> availableFunctions = await plugins.GetFunctionsAsync(plannerOptions, semanticQuery, logger, cancellationToken).ConfigureAwait(false);

        return string.Join("\n\n", availableFunctions.Select(x => x.ToManualString()));
    }

    /// <summary>
    /// Returns a string containing the manual for all available functions in a JSON Schema format.
    /// </summary>
    /// <param name="plugins">The plugins.</param>
    /// <param name="plannerOptions">The planner options.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="logger">The logger to use for logging.</param>
    /// <param name="includeOutputSchema">Indicates if the output or return type of the function should be included in the schema.</param>
    /// <param name="nameDelimiter">The delimiter to use between the plugin name and the function name.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    internal static async Task<string> GetJsonSchemaFunctionsManualAsync(
        this IReadOnlyKernelPluginCollection plugins,
        PlannerOptions plannerOptions,
        string? semanticQuery = null,
        ILogger? logger = null,
        bool includeOutputSchema = true,
        string nameDelimiter = "-",
        CancellationToken cancellationToken = default)
    {
        IEnumerable<KernelFunctionMetadata> availableFunctions = await plugins.GetFunctionsAsync(plannerOptions, semanticQuery, logger, cancellationToken).ConfigureAwait(false);
        var manuals = availableFunctions.Select(x => x.ToJsonSchemaFunctionView(includeOutputSchema));
        return JsonSerializer.Serialize(manuals);
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded plugins and functions.
    /// </summary>
    /// <param name="plugins">The function provider.</param>
    /// <param name="plannerOptions">The planner options.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="logger">The logger to use for logging.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded plugins and functions.</returns>
    internal static async Task<IEnumerable<KernelFunctionMetadata>> GetFunctionsAsync(
        this IReadOnlyKernelPluginCollection plugins,
        PlannerOptions plannerOptions,
        string? semanticQuery,
        ILogger? logger,
        CancellationToken cancellationToken)
    {
        return plannerOptions.GetAvailableFunctionsAsync is null ?
            await plugins.GetAvailableFunctionsAsync(plannerOptions, semanticQuery, logger, cancellationToken).ConfigureAwait(false) :
            await plannerOptions.GetAvailableFunctionsAsync(plannerOptions, semanticQuery, cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded plugins and functions.
    /// </summary>
    /// <param name="plugins">The function provider.</param>
    /// <param name="plannerOptions">The planner options.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="logger">The logger to use for logging.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded plugins and functions.</returns>
    internal static async Task<IEnumerable<KernelFunctionMetadata>> GetAvailableFunctionsAsync(
        this IReadOnlyKernelPluginCollection plugins,
        PlannerOptions plannerOptions,
        string? semanticQuery = null,
        ILogger? logger = null,
        CancellationToken cancellationToken = default)
    {
        var functionsView = plugins.GetFunctionsMetadata();

        var availableFunctions = functionsView
            .Where(s => !plannerOptions.ExcludedPlugins.Contains(s.PluginName, StringComparer.OrdinalIgnoreCase)
                && !plannerOptions.ExcludedFunctions.Contains(s.Name, StringComparer.OrdinalIgnoreCase))
            .ToList();

        List<KernelFunctionMetadata>? result = null;
        var semanticMemoryConfig = plannerOptions.SemanticMemoryConfig;
        if (string.IsNullOrEmpty(semanticQuery) || semanticMemoryConfig is null || semanticMemoryConfig.Memory is NullMemory)
        {
            // If no semantic query is provided, return all available functions.
            // If a Memory provider has not been registered, return all available functions.
            result = availableFunctions;
        }
        else
        {
            result = new List<KernelFunctionMetadata>();

            // Remember functions in memory so that they can be searched.
            await RememberFunctionsAsync(semanticMemoryConfig.Memory, availableFunctions, cancellationToken).ConfigureAwait(false);

            // Search for functions that match the semantic query.
            var memories = semanticMemoryConfig.Memory.SearchAsync(
                PlannerMemoryCollectionName,
                semanticQuery!,
                semanticMemoryConfig.MaxRelevantFunctions,
                semanticMemoryConfig.RelevancyThreshold ?? 0.0,
                cancellationToken: cancellationToken);

            // Add functions that were found in the search results.
            result.AddRange(await GetRelevantFunctionsAsync(availableFunctions, memories, logger ?? NullLogger.Instance, cancellationToken).ConfigureAwait(false));

            // Add any missing functions that were included but not found in the search results.
            var missingFunctions = semanticMemoryConfig.IncludedFunctions
                .Except(result.Select(x => (x.PluginName, x.Name))!)
                .Join(availableFunctions, f => f, af => (af.PluginName, af.Name), (_, af) => af);

            result.AddRange(missingFunctions);
        }

        return result
            .OrderBy(x => x.PluginName)
            .ThenBy(x => x.Name);
    }

    private static async Task<IEnumerable<KernelFunctionMetadata>> GetRelevantFunctionsAsync(
        IEnumerable<KernelFunctionMetadata> availableFunctions,
        IAsyncEnumerable<MemoryQueryResult> memories,
        ILogger logger,
        CancellationToken cancellationToken = default)
    {
        var relevantFunctions = new List<KernelFunctionMetadata>();
        await foreach (var memoryEntry in memories.WithCancellation(cancellationToken))
        {
            var function = availableFunctions.FirstOrDefault(x => x.ToFullyQualifiedName() == memoryEntry.Metadata.Id);
            if (function != null)
            {
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
    /// <param name="memory">The memory provided to store the functions to.</param>
    /// <param name="availableFunctions">The available functions to save.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    private static async Task RememberFunctionsAsync(
        ISemanticTextMemory memory,
        List<KernelFunctionMetadata> availableFunctions,
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
