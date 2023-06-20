// Copyright (c) Microsoft. All rights reserved.
package com.microsoft.semantickernel.coreskills;

import com.microsoft.semantickernel.memory.SemanticTextMemory;
import com.microsoft.semantickernel.orchestration.SKContext;
import com.microsoft.semantickernel.skilldefinition.annotations.DefineSKFunction;
import com.microsoft.semantickernel.skilldefinition.annotations.SKFunctionParameters;

import reactor.core.publisher.Mono;

/// <summary>
/// TextMemorySkill provides a skill to save or recall information from the long or short term
// memory.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("memory", new TextMemorySkill());
/// Examples:
/// SKContext["input"] = "what is the capital of France?"
/// {{memory.recall $input }} => "Paris"
/// </example>
public class TextMemorySkill {
    /// <summary>
    /// Name of the context variable used to specify which memory collection to use.
    /// </summary>
    public static final String collectionParam = "collection";

    /// <summary>
    /// Name of the context variable used to specify memory search relevance score.
    /// </summary>
    public static final String RelevanceParam = "relevance";

    /// <summary>
    /// Name of the context variable used to specify a unique key associated with stored
    // information.
    /// </summary>
    public static final String KeyParam = "key";

    /// <summary>
    /// Name of the context variable used to specify the number of memories to recall
    /// </summary>
    public static final String LimitParam = "limit";

    public static final String DefaultCollection = "generic";
    public static final String DefaultRelevance = "0.75";
    public static final String DefaultLimit = "1";

    /// <summary>
    /// Key-based lookup for a specific memory
    /// </summary>
    /// <example>
    /// SKContext[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.retrieve }}
    /// </example>
    /// <param name="context">Contains the 'collection' containing the memory to retrieve and the
    // `key` associated with it.</param>

    @DefineSKFunction(description = "Key-based lookup for a specific memory", name = "Retrieve")
    public Mono<String> retrieveAsync(
            SKContext context,
            @SKFunctionParameters(
                            name = collectionParam,
                            description =
                                    "Memories collection associated with the memory to retrieve",
                            defaultValue = DefaultCollection)
                    String collection,
            @SKFunctionParameters(
                            name = KeyParam,
                            description = "The key associated with the memory to retrieve")
                    String key) {

        SemanticTextMemory memory = context.getSemanticMemory();

        if (memory == null) {
            return Mono.error(new RuntimeException("Memory not present"));
        }

        return memory.getAsync(collection, key, false)
                .map(it -> it.getMetadata().getText())
                .defaultIfEmpty("");

        // var collection = context.Variables.ContainsKey(CollectionParam) ?
        // context[CollectionParam] :
        // DefaultCollection;
        // Verify.NotEmpty(collection, "Memory collection not defined");

        // var key = context.Variables.ContainsKey(KeyParam) ? context[KeyParam] : string.Empty;
        // Verify.NotEmpty(key, "Memory key not defined");

        // context.Log.LogTrace("Recalling memory with key '{0}' from collection '{1}'", key,
        // collection);

        // return context.Memory.GetAsync(collection, key);

        // return memory ?.Metadata.Text ??string.Empty;
    }

    @DefineSKFunction(description = "Save information to semantic memory", name = "Save")
    public Mono<SKContext> saveAsync(
            @SKFunctionParameters(
                            name = KeyParam,
                            description = "The information to save",
                            defaultValue = "",
                            type = String.class)
                    String text,
            @SKFunctionParameters(
                            name = collectionParam,
                            description =
                                    "Memories collection associated with the information to save",
                            defaultValue = DefaultCollection,
                            type = String.class)
                    String collection,
            @SKFunctionParameters(
                            name = KeyParam,
                            description = "The key associated with the information to save",
                            defaultValue = "",
                            type = String.class)
                    String key,
            SKContext context) {

        return Mono.empty();
        /*
        context
                .getSemanticMemory()
                .saveInformationAsync(collection, text, key, null, null)
                .map(it -> {
                    SKContext
                            .build(
                                    context.getVariables(),
                                    it,
                                    context.getSkills()
                            )
                });

         */

    }

    /*
    /// <summary>
    /// Semantic search and return up to N memories related to the input text
    /// </summary>
    /// <example>
    /// SKContext["input"] = "what is the capital of France?"
    /// {{memory.recall $input }} => "Paris"
    /// </example>
    /// <param name="text">The input text to find related memories for</param>
    /// <param name="context">Contains the 'collection' to search for the topic and 'relevance' score</param>
    [SKFunction("Semantic search and return up to N memories related to the input text")]
    [SKFunctionName("Recall")]
    [SKFunctionInput(Description = "The input text to find related memories for")]
    [SKFunctionContextParameter(Name = CollectionParam, Description = "Memories collection to search", DefaultValue = DefaultCollection)]
    [SKFunctionContextParameter(Name = RelevanceParam, Description = "The relevance score, from 0.0 to 1.0, where 1.0 means perfect match",
        DefaultValue = DefaultRelevance)]
    [SKFunctionContextParameter(Name = LimitParam, Description = "The maximum number of relevant memories to recall", DefaultValue = DefaultLimit)]
    public string Recall(string text, SKContext context)
    {
        var collection = context.Variables.ContainsKey(CollectionParam) ? context[CollectionParam] : DefaultCollection;
        Verify.NotEmpty(collection, "Memories collection not defined");

        var relevance = context.Variables.ContainsKey(RelevanceParam) ? context[RelevanceParam] : DefaultRelevance;
        if (string.IsNullOrWhiteSpace(relevance)) { relevance = DefaultRelevance; }

        var limit = context.Variables.ContainsKey(LimitParam) ? context[LimitParam] : DefaultLimit;
        if (string.IsNullOrWhiteSpace(limit)) { relevance = DefaultLimit; }

        context.Log.LogTrace("Searching memories in collection '{0}', relevance '{1}'", collection, relevance);

        // TODO: support locales, e.g. "0.7" and "0,7" must both work
        int limitInt = int.Parse(limit, CultureInfo.InvariantCulture);
        var memories = context.Memory
            .SearchAsync(collection, text, limitInt, minRelevanceScore: float.Parse(relevance, CultureInfo.InvariantCulture))
            .ToEnumerable();

        context.Log.LogTrace("Done looking for memories in collection '{0}')", collection);

        string resultString;

        if (limitInt == 1)
        {
            var memory = memories.FirstOrDefault();
            resultString = (memory != null) ? memory.Metadata.Text : string.Empty;
        }
        else
        {
            resultString = JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text));
        }

        if (resultString.Length == 0)
        {
            context.Log.LogWarning("Memories not found in collection: {0}", collection);
        }

        return resultString;
    }

    /// <summary>
    /// Save information to semantic memory
    /// </summary>
    /// <example>
    /// SKContext["input"] = "the capital of France is Paris"
    /// SKContext[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.save $input }}
    /// </example>
    /// <param name="text">The information to save</param>
    /// <param name="context">Contains the 'collection' to save the information and unique 'key' to associate it with.</param>
    [SKFunction("Save information to semantic memory")]
    [SKFunctionName("Save")]
    [SKFunctionInput(Description = "The information to save")]
    [SKFunctionContextParameter(Name = CollectionParam, Description = "Memories collection associated with the information to save",
        DefaultValue = DefaultCollection)]
    [SKFunctionContextParameter(Name = KeyParam, Description = "The key associated with the information to save")]
    public async Task SaveAsync(string text, SKContext context)
    {
        var collection = context.Variables.ContainsKey(CollectionParam) ? context[CollectionParam] : DefaultCollection;
        Verify.NotEmpty(collection, "Memory collection not defined");

        var key = context.Variables.ContainsKey(KeyParam) ? context[KeyParam] : string.Empty;
        Verify.NotEmpty(key, "Memory key not defined");

        context.Log.LogTrace("Saving memory to collection '{0}'", collection);

        await context.Memory.SaveInformationAsync(collection, text: text, id: key);
    }

    /// <summary>
    /// Remove specific memory
    /// </summary>
    /// <example>
    /// SKContext[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.remove }}
    /// </example>
    /// <param name="context">Contains the 'collection' containing the memory to remove.</param>
    [SKFunction("Remove specific memory")]
    [SKFunctionName("Remove")]
    [SKFunctionContextParameter(Name = CollectionParam, Description = "Memories collection associated with the memory to remove",
        DefaultValue = DefaultCollection)]
    [SKFunctionContextParameter(Name = KeyParam, Description = "The key associated with the memory to remove")]
    public async Task RemoveAsync(SKContext context)
    {
        var collection = context.Variables.ContainsKey(CollectionParam) ? context[CollectionParam] : DefaultCollection;
        Verify.NotEmpty(collection, "Memory collection not defined");

        var key = context.Variables.ContainsKey(KeyParam) ? context[KeyParam] : string.Empty;
        Verify.NotEmpty(key, "Memory key not defined");

        context.Log.LogTrace("Removing memory from collection '{0}'", collection);

        await context.Memory.RemoveAsync(collection, key);
    }*/
}
