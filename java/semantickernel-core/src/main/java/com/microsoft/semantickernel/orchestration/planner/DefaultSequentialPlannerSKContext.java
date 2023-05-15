// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.orchestration.planner;

import com.microsoft.semantickernel.memory.MemoryQueryResult;
import com.microsoft.semantickernel.memory.NullMemory;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.*;
import com.microsoft.semantickernel.planner.SequentialPlannerRequestSettings;
import com.microsoft.semantickernel.planner.SequentialPlannerSKContext;
import com.microsoft.semantickernel.skilldefinition.ReadOnlySkillCollection;

import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.util.*;
import java.util.function.Supplier;
import java.util.stream.Collectors;

import javax.annotation.Nullable;

public class DefaultSequentialPlannerSKContext extends AbstractSKContext<SequentialPlannerSKContext>
        implements SequentialPlannerSKContext {
    public DefaultSequentialPlannerSKContext(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        super(variables, memory, skills);
    }

    @Override
    public SequentialPlannerSKContext build(
            ContextVariables variables,
            @Nullable SemanticTextMemory memory,
            @Nullable Supplier<ReadOnlySkillCollection> skills) {
        return new DefaultSequentialPlannerSKContext(variables, memory, skills);
    }

    /// <summary>
    /// Returns a string containing the manual for all available functions.
    /// </summary>
    /// <param name="context">The SKContext to get the functions manual for.</param>
    /// <param name="semanticQuery">The semantic query for finding relevant registered
    // functions</param>
    /// <param name="config">The planner skill config.</param>
    /// <returns>A string containing the manual for all available functions.</returns>
    @Override
    public Mono<String> getFunctionsManualAsync(
            @Nullable String semanticQuery, @Nullable SequentialPlannerRequestSettings config) {
        if (config == null) {
            config = new SequentialPlannerRequestSettings();
        }

        Mono<SortedSet<SKFunction<?, ?>>> functions =
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
    public Mono<SortedSet<SKFunction<?, ?>>> getAvailableFunctionsAsync(
            SequentialPlannerRequestSettings config, @Nullable String semanticQuery) {
        Set<String> excludedSkills = config.getExcludedSkills();
        Set<String> excludedFunctions = config.getExcludedFunctions();
        Set<String> includedFunctions = config.getIncludedFunctions();

        // context.ThrowIfSkillCollectionNotSet();

        ReadOnlySkillCollection skills = getSkills();
        List<SKFunction<?, ?>> functions;
        if (skills != null) {
            functions = skills.getAllFunctions().getAll();
        } else {
            functions = Collections.emptyList();
        }

        List<SKFunction<?, ?>> availableFunctions =
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

        Comparator<SKFunction<?, ?>> comparator =
                Comparator.<SKFunction<?, ?>, String>comparing(SKFunction::getSkillName)
                        .thenComparing(SKFunction::getName);

        if (semanticQuery == null
                || semanticQuery.isEmpty()
                || getSemanticMemory() == null
                || getSemanticMemory() instanceof NullMemory
                || config.getRelevancyThreshold() == null) {
            // If no semantic query is provided, return all available functions.
            // If a Memory provider has not been registered, return all available functions.
            TreeSet<SKFunction<?, ?>> result = new TreeSet<>(comparator);
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
                                    return Mono.just(
                                            new ArrayList<
                                                    SKFunction<
                                                            Void, SequentialPlannerSKContext>>());
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

                                List<SKFunction<?, ?>> missingFunctions =
                                        getMissingFunctions(
                                                includedFunctions, availableFunctions, added);

                                ArrayList<SKFunction<?, ?>> res = new ArrayList<>(memories);
                                res.addAll(missingFunctions);
                                return res;
                            })
                    .map(
                            res -> {
                                TreeSet<SKFunction<?, ?>> result = new TreeSet<>(comparator);
                                result.addAll(availableFunctions);
                                return result;
                            });
        }
    }

    private static List<SKFunction<?, ?>> getMissingFunctions(
            Set<String> includedFunctions,
            List<SKFunction<?, ?>> availableFunctions,
            List<String> added) {
        return includedFunctions.stream()
                .filter(func -> !added.contains(func))
                .flatMap(
                        missing ->
                                availableFunctions.stream()
                                        .filter(it -> it.getName().equals(missing)))
                .collect(Collectors.toList());
    }
    /*

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
        var functions = await context.GetAvailableFunctionsAsync(config, semanticQuery).ConfigureAwait(false);

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

        context.ThrowIfSkillCollectionNotSet();

        var functionsView = context.Skills!.GetFunctionsView();

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
    }*/

    public Mono<? extends List<? extends SKFunction<?, ?>>> getRelevantFunctionsAsync(
            List<SKFunction<?, ?>> availableFunctions, List<MemoryQueryResult> memories) {
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
    Mono<DefaultSequentialPlannerSKContext> rememberFunctionsAsync(
            List<SKFunction<?, ?>> availableFunctions) {
        // Check if the functions have already been saved to memory.
        if (getVariables().asMap().containsKey(PlanSKFunctionsAreRemembered)) {
            return Mono.just(this);
        }

        SemanticTextMemory memory = getSemanticMemory();

        if (memory == null) {
            return Mono.just(
                    new DefaultSequentialPlannerSKContext(
                            (ContextVariables) setVariable(PlanSKFunctionsAreRemembered, "true"),
                            null,
                            this::getSkills));
        }

        return Flux.fromIterable(availableFunctions)
                .flatMap(
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
                .reduce(memory, SemanticTextMemory::merge)
                .map(
                        newMemory -> {
                            return new DefaultSequentialPlannerSKContext(
                                    (ContextVariables)
                                            setVariable(PlanSKFunctionsAreRemembered, "true"),
                                    newMemory,
                                    this::getSkills);
                        });
    }
}
