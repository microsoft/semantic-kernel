// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner;

import com.microsoft.semantickernel.orchestration.SKContext;

import reactor.core.publisher.Mono;

import javax.annotation.Nullable;

public interface SequentialPlannerSKContext extends SKContext<SequentialPlannerSKContext> {

    public static final String PlannerMemoryCollectionName = "Planning.SKFunctionsManual";

    public static final String PlanSKFunctionsAreRemembered = "Planning.SKFunctionsAreRemembered";

    public Mono<String> getFunctionsManualAsync(
            @Nullable String semanticQuery, @Nullable SequentialPlannerRequestSettings config);
    /*
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
        if (context.Variables.Get(PlanSKFunctionsAreRemembered, out var _))
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
     */
}
