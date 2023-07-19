// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Planning.Sequential;
using Microsoft.SemanticKernel.SkillDefinition;

#pragma warning disable IDE0130
// ReSharper disable once CheckNamespace - Using NS of SKContext
namespace Microsoft.SemanticKernel.Orchestration;
#pragma warning restore IDE0130

public static class SKContextSequentialPlannerExtensions
{
    internal const string PlannerMemoryCollectionName = "Planning.SKFunctionsManual";

    internal const string PlanSKFunctionsAreRemembered = "Planning.SKFunctionsAreRemembered";

    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="context">The SKContext to get the functions manual for.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <param name="config">The planner skill config.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    public static async Task<string> GetFunctionsManualAsync(
        this SKContext context,
        string? semanticQuery = null,
        SequentialPlannerConfig? config = null)
    {
        config ??= new SequentialPlannerConfig();

        // Use configured function provider if available, otherwise use the default SKContext function provider.
        IOrderedEnumerable<FunctionView> functions = config.GetAvailableFunctionsAsync is null ?
            await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(false) :
            await config.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(false);

        return string.Join("\n\n", functions.Select(x => x.ToManualString()));
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and the excluded skills and functions.
    /// </summary>
    /// <param name="context">The SKContext</param>
    /// <param name="config">The planner config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered functions</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and the excluded skills and functions.</returns>
    public static async Task<IOrderedEnumerable<FunctionView>> GetAvailableFunctionsAsync(
        this SKContext context,
        SequentialPlannerConfig config,
        string? semanticQuery = null)
    {
        var excludedSkills = config.ExcludedSkills ?? new();
        var excludedFunctions = config.ExcludedFunctions ?? new();
        var includedFunctions = config.IncludedFunctions ?? new();

        if (context.Skills == null)
        {
            throw new SKException("Skill collection not found in the context");
        }

        var functionsView = context.Skills.GetFunctionsView();

        var availableFunctions = functionsView.SemanticFunctions
            .Concat(functionsView.NativeFunctions)
            .SelectMany(x => x.Value)
            .Where(s => !excludedSkills.Contains(s.SkillName) && !excludedFunctions.Contains(s.Name))
            .ToList();

        List<FunctionView>? result = null;
        if (string.IsNullOrEmpty(semanticQuery) || context.Memory is NullMemory || config.RelevancyThreshold is null)
        {
            // If no semantic query is provided, return all available functions.
            // If a Memory provider has not been registered, return all available functions.
            result = availableFunctions;
        }
        else
        {
            result = new List<FunctionView>();

            // Remember functions in memory so that they can be searched.
            await RememberFunctionsAsync(context, availableFunctions).ConfigureAwait(false);

            // Search for functions that match the semantic query.
            var memories = context.Memory.SearchAsync(PlannerMemoryCollectionName, semanticQuery!, config.MaxRelevantFunctions, config.RelevancyThreshold.Value,
                false,
                context.CancellationToken);

            // Add functions that were found in the search results.
            result.AddRange(await GetRelevantFunctionsAsync(context, availableFunctions, memories).ConfigureAwait(false));

            // Add any missing functions that were included but not found in the search results.
            var missingFunctions = includedFunctions
                .Except(result.Select(x => x.Name))
                .Join(availableFunctions, f => f, af => af.Name, (_, af) => af);

            result.AddRange(missingFunctions);
        }

        return result
            .OrderBy(x => x.SkillName)
            .ThenBy(x => x.Name);
    }

    public static async Task<IEnumerable<FunctionView>> GetRelevantFunctionsAsync(SKContext context, IEnumerable<FunctionView> availableFunctions,
        IAsyncEnumerable<MemoryQueryResult> memories)
    {
        var relevantFunctions = new ConcurrentBag<FunctionView>();
        await foreach (var memoryEntry in memories.WithCancellation(context.CancellationToken))
        {
            var function = availableFunctions.FirstOrDefault(x => x.ToFullyQualifiedName() == memoryEntry.Metadata.Id);
            if (function != null)
            {
                context.Log.LogDebug("Found relevant function. Relevance Score: {0}, Function: {1}", memoryEntry.Relevance,
                    function.ToFullyQualifiedName());
                relevantFunctions.Add(function);
            }
        }

        return relevantFunctions;
    }

    /// <summary>
    /// Saves all available functions to memory.
    /// </summary>
    /// <param name="context">The SKContext to save the functions to.</param>
    /// <param name="availableFunctions">The available functions to save.</param>
    internal static async Task RememberFunctionsAsync(SKContext context, List<FunctionView> availableFunctions)
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
            var memoryEntry = await context.Memory.GetAsync(collection: PlannerMemoryCollectionName, key: key, withEmbedding: false,
                cancellationToken: context.CancellationToken).ConfigureAwait(false);
            if (memoryEntry == null)
            {
                // TODO It'd be nice if the minRelevanceScore could be a parameter for each item that was saved to memory
                // As folks may want to tune their functions to be more or less relevant.
                // Memory now supports these such strategies.
                await context.Memory.SaveInformationAsync(collection: PlannerMemoryCollectionName, text: textToEmbed, id: key, description: description,
                    additionalMetadata: string.Empty, cancellationToken: context.CancellationToken).ConfigureAwait(false);
            }
        }

        // Set a flag to indicate that the functions have been saved to memory.
        context.Variables.Set(PlanSKFunctionsAreRemembered, "true");
    }
}
