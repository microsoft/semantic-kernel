// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.planner.sequentialplanner;

import com.microsoft.semantickernel.memory.MemoryQueryResult;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.orchestration.SKFunction;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.*;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

public class DefaultSequentialPlannerSKContext {
    public static final String PlannerMemoryCollectionName = "Planning.SKFunctionsManual";

    public static final String PlanSKFunctionsAreRemembered = "Planning.SKFunctionsAreRemembered";
    private final SKContext delegate;

    public DefaultSequentialPlannerSKContext(SKContext delegate) {
        this.delegate = delegate;
    }

    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="context">The SKContext to get the functions manual for.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered
    // functions</param>
    /// <param name="config">The planner skill config.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    public Mono<String> getFunctionsManualAsync(
            @Nullable String semanticQuery, @Nullable SequentialPlannerRequestSettings config) {
        if (config == null) {
            config = new SequentialPlannerRequestSettings();
        }

        Mono<SortedSet<SKFunction<?>>> functions =
                getAvailableFunctionsAsync(config, semanticQuery);

        return functions.map(
                funcs ->
                        funcs.stream()
                                .map(SKFunction::toManualString)
                                .collect(Collectors.joining("\n\n")));
    }

    /// <summary>
    /// Returns a list of functions that are available to the user based on the semantic query and
    // the excluded skills and functions.
    /// </summary>
    /// <param name="context">The SKContext</param>
    /// <param name="config">The planner config.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered
    // functions</param>
    /// <returns>A list of functions that are available to the user based on the semantic query and
    // the excluded skills and functions.</returns>
    public Mono<SortedSet<SKFunction<?>>> getAvailableFunctionsAsync(
            SequentialPlannerRequestSettings config, @Nullable String semanticQuery) {
        Set<String> excludedSkills = config.getExcludedSkills();
        Set<String> excludedFunctions = config.getExcludedFunctions();
        Set<String> includedFunctions = config.getIncludedFunctions();

        // context.ThrowIfSkillCollectionNotSet();

        ReadOnlySkillCollection skills = delegate.getSkills();
        List<SKFunction<?>> functions;
        if (skills != null) {
            functions = skills.getAllFunctions().getAll();
        } else {
            functions = Collections.emptyList();
        }

        List<SKFunction<?>> availableFunctions =
                functions.stream()
                        /*
                        // Is there any function that should be excluded?
                        .filter(
                                it ->
                                        it instanceof SemanticSKFunction
                                                || it instanceof NativeSKFunction)

                         */
                        .filter(
                                s ->
                                        !excludedSkills.contains(s.getSkillName())
                                                && !excludedFunctions.contains(s.getName()))
                        .collect(Collectors.toList());

        Comparator<SKFunction<?>> comparator =
                Comparator.<SKFunction<?>, String>comparing(SKFunction::getSkillName)
                        .thenComparing(SKFunction::getName);

        if (semanticQuery == null
                || semanticQuery.isEmpty()
                || delegate.getSemanticMemory() == null
                || delegate.getSemanticMemory() instanceof NullMemory
                || config.getRelevancyThreshold() == null) {
            // If no semantic query is provided, return all available functions.
            // If a Memory provider has not been registered, return all available functions.
            TreeSet<SKFunction<?>> result = new TreeSet<>(comparator);
            result.addAll(availableFunctions);
            return Mono.just(result);
        } else {
            // Remember functions in memory so that they can be searched.
            return rememberFunctionsAsync(availableFunctions)
                    .flatMap(
                            updatedContext -> {
                                SemanticTextMemory updatedMemory =
                                        updatedContext.getSemanticMemory();
                                if (updatedMemory == null) {
                                    return Mono.just(new ArrayList<SKFunction<Void>>());
                                }
                                // Search for functions that match the semantic query.
                                return updatedMemory
                                        .searchAsync(
                                                PlannerMemoryCollectionName,
                                                semanticQuery,
                                                config.getMaxRelevantFunctions(),
                                                config.getRelevancyThreshold(),
                                                false)
                                        .flatMap(
                                                memories ->
                                                        getRelevantFunctionsAsync(
                                                                availableFunctions, memories));
                            })
                    .map(
                            memories -> {
                                List<String> added =
                                        memories.stream()
                                                .map(SKFunction::getName)
                                                .collect(Collectors.toList());

                                List<SKFunction<?>> missingFunctions =
                                        getMissingFunctions(
                                                includedFunctions, availableFunctions, added);

                                ArrayList<SKFunction<?>> res = new ArrayList<>(memories);
                                res.addAll(missingFunctions);
                                return res;
                            })
                    .map(
                            res -> {
                                TreeSet<SKFunction<?>> result = new TreeSet<>(comparator);
                                result.addAll(availableFunctions);
                                return result;
                            });
        }
    }

    private static List<SKFunction<?>> getMissingFunctions(
            Set<String> includedFunctions,
            List<SKFunction<?>> availableFunctions,
            List<String> added) {
        return includedFunctions.stream()
                .filter(func -> !added.contains(func))
                .flatMap(
                        missing ->
                                availableFunctions.stream()
                                        .filter(it -> it.getName().equals(missing)))
                .collect(Collectors.toList());
    }

    public Mono<? extends List<? extends SKFunction<?>>> getRelevantFunctionsAsync(
            List<SKFunction<?>> availableFunctions, List<MemoryQueryResult> memories) {
        return Flux.fromIterable(memories)
                .map(
                        memoryEntry ->
                                availableFunctions.stream()
                                        .filter(
                                                it ->
                                                        Objects.equals(
                                                                it.toFullyQualifiedName(),
                                                                memoryEntry.getMetadata().getId()))
                                        .findFirst()
                                        .orElse(null))
                .filter(Objects::nonNull)
                .collectList();
    }

    /// <summary>
    /// Saves all available functions to memory.
    /// </summary>
    /// <param name="context">The SKContext to save the functions to.</param>
    /// <param name="availableFunctions">The available functions to save.</param>
    Mono<SKContext> rememberFunctionsAsync(List<SKFunction<?>> availableFunctions) {
        // Check if the functions have already been saved to memory.
        if (delegate.getVariables().asMap().containsKey(PlanSKFunctionsAreRemembered)) {
            return Mono.just(delegate);
        }

        SemanticTextMemory memory = delegate.getSemanticMemory();

        if (memory == null) {
            delegate.setVariable(PlanSKFunctionsAreRemembered, "true");
            return Mono.just(delegate);
        }

        return Flux.fromIterable(availableFunctions)
                .concatMap(
                        function -> {
                            String functionName = function.toFullyQualifiedName();
                            String key = functionName;
                            String description =
                                    function.getDescription() == null
                                                    || function.getDescription().isEmpty()
                                            ? functionName
                                            : function.getDescription();
                            String textToEmbed = function.toEmbeddingString();

                            // It'd be nice if there were a saveIfNotExists method on the memory
                            // interface
                            return memory.getAsync(PlannerMemoryCollectionName, key, false)
                                    .filter(Objects::nonNull)
                                    .flatMap(
                                            memoryEntry -> {
                                                // TODO It'd be nice if the minRelevanceScore could
                                                // be a parameter for each item that was saved to
                                                // memory
                                                // As folks may want to tune their functions to be
                                                // more or less relevant.
                                                // Memory now supports these such strategies.
                                                return memory.saveInformationAsync(
                                                        PlannerMemoryCollectionName,
                                                        textToEmbed,
                                                        key,
                                                        description,
                                                        "");
                                            })
                                    .flatMap(
                                            newKey ->
                                                    memory.getAsync(
                                                            PlannerMemoryCollectionName,
                                                            newKey,
                                                            true));
                        })
                .ignoreElements()
                .map(
                        newMemory -> {
                            delegate.setVariable(PlanSKFunctionsAreRemembered, "true");
                            return delegate;
                        });
    }
}
