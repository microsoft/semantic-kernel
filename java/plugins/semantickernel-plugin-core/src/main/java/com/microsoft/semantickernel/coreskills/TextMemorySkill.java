// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.builders.SKBuilders;
import com.microsoft.semantickernel.memory.MemoryException;
import com.microsoft.semantickernel.memory.MemoryQueryResult;
import com.microsoft.semantickernel.memory.MemoryRecordMetadata;
import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;
import java.util.List;
import java.util.stream.Collectors;
import javax.annotation.Nonnull;
import reactor.core.publisher.Mono;

/**
 * TextMemorySkill provides a skill to save or recall information from the long or short term.
 * Usage: {@code kernel.ImportSkill(new TextMemorySkill(), "memory");} Example: {@code
 * {{memory.recall "what is the capital of France?" }} => "Paris"}
 */
public class TextMemorySkill {

    /** Name of the context variable used to specify which memory collection to use. */
    public static final String COLLECTION_PARAM = "collection";

    /** Name of the context variable used to specify the information to store. */
    public static final String INFO_PARAM = "info";

    /** Name of the context variable used to specify the input to the skill. */
    public static final String INPUT_PARAM = "input";

    /** Name of the context variable used to specify memory search relevance score. */
    public static final String RELEVANCE_PARAM = "relevance";

    /**
     * Name of the context variable used to specify a unique key associated with stored information.
     */
    public static final String KEY_PARAM = "key";

    /** Name of the context variable used to specify the number of memories to recall */
    public static final String LIMIT_PARAM = "limit";

    /** Default value for the collection name. */
    public static final String DEFAULT_COLLECTION = "generic";

    /** Default value for the relevance score. */
    public static final String DEFAULT_RELEVANCE = "0.75";

    /** Default value for the limit. */
    public static final String DEFAULT_LIMIT = "1";

    /**
     * Key-based lookup for a specific memory.
     *
     * @param collection The collection containing the memory to retrieve
     * @param key The key associated with the memory to retrieve
     * @param context The context containing the semantic memory
     * @return The memory associated with the key
     */
    @DefineSKFunction(description = "Key-based lookup for a specific memory", name = "Retrieve")
    public Mono<String> retrieveAsync(
            @SKFunctionParameters(
                            name = COLLECTION_PARAM,
                            description =
                                    "Memories collection associated with the memory to retrieve",
                            defaultValue = DEFAULT_COLLECTION)
                    String collection,
            @SKFunctionParameters(
                            name = KEY_PARAM,
                            description = "The key associated with the memory to retrieve")
                    String key,
            SKContext context) {

        SemanticTextMemory memory = context.getSemanticMemory();

        if (memory == null) {
            return Mono.error(new RuntimeException("Memory not present"));
        }

        return memory.getAsync(collection, key, false)
                .map(it -> it.getMetadata().getText())
                .defaultIfEmpty("");
    }

    /**
     * Save information to semantic memory.
     *
     * @param info The information to save
     * @param collection Memories collection associated with the information to save
     * @param key The key associated with the information to save
     * @param context The context containing the semantic memory
     * @return The key associated with the saved information
     */
    @DefineSKFunction(description = "Save information to semantic memory", name = "Save")
    public Mono<SKContext> saveAsync(
            @SKFunctionParameters(
                            name = INFO_PARAM,
                            description = "The information to save",
                            defaultValue = "",
                            type = String.class)
                    String info,
            @SKFunctionParameters(
                            name = COLLECTION_PARAM,
                            description =
                                    "Memories collection associated with the information to save",
                            defaultValue = DEFAULT_COLLECTION,
                            type = String.class)
                    String collection,
            @SKFunctionParameters(
                            name = KEY_PARAM,
                            description = "The key associated with the information to save",
                            defaultValue = "",
                            type = String.class)
                    String key,
            SKContext context) {

        SemanticTextMemory memory = context.getSemanticMemory();
        if (memory == null) {
            return Mono.error(
                    new MemoryException(MemoryException.ErrorCodes.UNKNOWN, "Memory not present"));
        }

        return memory.saveInformationAsync(collection, info, key, null, null)
                .map(
                        it -> {
                            context.setVariable(TextMemorySkill.KEY_PARAM, it);
                            return SKBuilders.context()
                                    .with(context.getVariables())
                                    .with(context.getSkills())
                                    .with(context.getSemanticMemory())
                                    .build();
                        });
    }

    /**
     * Semantic search and return up to N memories related to the input text
     *
     * @param input The input text to find related memories for
     * @param collection Memories collection to search
     * @param relevance The relevance score, from 0.0 to 1.0, where 1.0 means perfect match
     * @param limit The maximum number of relevant memories to recall
     * @param context Contains the memory to search
     * @return The list of memories related to the input text
     */
    @DefineSKFunction(
            description = "Semantic search and return up to N memories related to the input text",
            name = "Recall")
    public Mono<List<String>> recallAsync(
            @SKFunctionParameters(
                            name = INPUT_PARAM,
                            description = "The information to recall",
                            defaultValue = "",
                            type = String.class)
                    @Nonnull
                    String input,
            @SKFunctionParameters(
                            name = COLLECTION_PARAM,
                            description =
                                    "Memories collection associated with the information to recall",
                            defaultValue = DEFAULT_COLLECTION,
                            type = String.class)
                    String collection,
            @SKFunctionParameters(
                            name = RELEVANCE_PARAM,
                            description =
                                    "The relevance score, from 0.0 to 1.0, where 1.0 means perfect"
                                            + " match",
                            defaultValue = DEFAULT_RELEVANCE,
                            type = Double.class)
                    double relevance,
            @SKFunctionParameters(
                            name = LIMIT_PARAM,
                            description = "The maximum number of relevant memories to recall",
                            defaultValue = DEFAULT_LIMIT,
                            type = Integer.class)
                    int limit,
            @Nonnull SKContext context) {

        SemanticTextMemory memory = context.getSemanticMemory();
        if (memory == null) {
            return Mono.error(
                    new MemoryException(MemoryException.ErrorCodes.UNKNOWN, "Memory not present"));
        }

        // Validate parameters
        if (collection == null || collection.trim().isEmpty()) {
            collection = context.getVariables().get(TextMemorySkill.COLLECTION_PARAM);
            if (collection == null) collection = DEFAULT_COLLECTION;
        }
        final String _collection = collection;
        final double _relevance = Math.min(1.0, Math.max(0.0, relevance));
        final int _limit = Math.max(1, limit);

        // context.Log.LogTrace("Searching memories in collection '{0}', relevance '{1}'",
        // collection, relevance);

        // Search memory
        return memory.searchAsync(_collection, input, _limit, _relevance, false)
                .flatMap(
                        results -> {
                            List<String> memories =
                                    results.stream()
                                            .map(MemoryQueryResult::getMetadata)
                                            .map(MemoryRecordMetadata::getText)
                                            .collect(Collectors.toList());
                            return Mono.just(memories);
                        });
    }

    /**
     * Remove information from semantic memory
     *
     * @param collection Memories collection associated with the information to remove
     * @param key The key associated with the information to remove
     * @param context Contains the memory to remove
     * @return The reactive stream
     */
    @DefineSKFunction(description = "Remove information from semantic memory", name = "Remove")
    public Mono<Void> removeAsync(
            @SKFunctionParameters(
                            name = COLLECTION_PARAM,
                            description =
                                    "Memories collection associated with the information to remove",
                            defaultValue = DEFAULT_COLLECTION,
                            type = String.class)
                    String collection,
            @SKFunctionParameters(
                            name = KEY_PARAM,
                            description = "The key associated with the information to remove",
                            defaultValue = "",
                            type = String.class)
                    String key,
            SKContext context) {
        SemanticTextMemory memory = context.getSemanticMemory();
        if (memory == null) {
            return Mono.error(
                    new MemoryException(MemoryException.ErrorCodes.UNKNOWN, "Memory not present"));
        }

        return memory.removeAsync(collection, key);
    }
}
