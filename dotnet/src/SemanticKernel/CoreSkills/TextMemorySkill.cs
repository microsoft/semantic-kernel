// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.Globalization;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Orchestration;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.CoreSkills;

/// <summary>
/// TextMemorySkill provides a skill to save or recall information from the long or short term memory.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("memory", new TextMemorySkill());
/// Examples:
/// SKContext["input"] = "what is the capital of France?"
/// {{memory.recall $input }} => "Paris"
/// </example>
public class TextMemorySkill
{
    /// <summary>
    /// Name of the context variable used to specify which memory collection to use.
    /// </summary>
    public const string CollectionParam = "collection";

    /// <summary>
    /// Name of the context variable used to specify memory search relevance score.
    /// </summary>
    public const string RelevanceParam = "relevance";

    /// <summary>
    /// Name of the context variable used to specify a unique key associated with stored information.
    /// </summary>
    public const string KeyParam = "key";

    /// <summary>
    /// Name of the context variable used to specify the number of memories to recall
    /// </summary>
    public const string LimitParam = "limit";

    private const string DefaultCollection = "generic";
    private const string DefaultRelevance = "0.75";
    private const string DefaultLimit = "1";

    /// <summary>
    /// Key-based lookup for a specific memory
    /// </summary>
    /// <example>
    /// SKContext[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.retrieve }}
    /// </example>
    /// <param name="context">Contains the 'collection' containing the memory to retrieve and the `key` associated with it.</param>
    [SKFunction("Key-based lookup for a specific memory")]
    [SKFunctionName("Retrieve")]
    [SKFunctionContextParameter(Name = CollectionParam, Description = "Memories collection associated with the memory to retrieve",
        DefaultValue = DefaultCollection)]
    [SKFunctionContextParameter(Name = KeyParam, Description = "The key associated with the memory to retrieve")]
    public async Task<string> RetrieveAsync(SKContext context)
    {
        var collection = context.Variables.ContainsKey(CollectionParam) ? context[CollectionParam] : DefaultCollection;
        Verify.NotEmpty(collection, "Memory collection not defined");

        var key = context.Variables.ContainsKey(KeyParam) ? context[KeyParam] : string.Empty;
        Verify.NotEmpty(key, "Memory key not defined");

        context.Log.LogTrace("Recalling memory from collection '{0}'", collection);

        var memory = await context.Memory.GetAsync(collection, key);
        return memory != null ? memory.Text : string.Empty;
    }

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

        var limit = context.Variables.ContainsKey(LimitParam) ? context[LimitParam] : LimitParam;
        if (string.IsNullOrWhiteSpace(relevance)) { relevance = DefaultLimit; }

        context.Log.LogTrace("Searching memories for '{0}', collection '{1}', relevance '{2}'", text, collection, relevance);

        // TODO: support locales, e.g. "0.7" and "0,7" must both work
        var memories = context.Memory
            .SearchAsync(collection, text, limit: int.Parse(limit, CultureInfo.InvariantCulture), minRelevanceScore: float.Parse(relevance, CultureInfo.InvariantCulture))
            .ToEnumerable();

        context.Log.LogTrace("Memories found (collection: {0})", collection);
        var resultString = JsonSerializer.Serialize(memories.Select(x => x.Text));

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
    [SKFunctionContextParameter(Name = CollectionParam, Description = "Memories collection associated with the information to save", DefaultValue = DefaultCollection)]
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
    }
}
