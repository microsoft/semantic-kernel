// Copyright (c) Microsoft. All rights reserved.

using System.Globalization;
using System.Linq;
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

    private const string DefaultCollection = "generic";
    private const string DefaultRelevance = "0.75";

    /// <summary>
    /// Recall a fact from the long term memory
    /// </summary>
    /// <example>
    /// SKContext["input"] = "what is the capital of France?"
    /// {{memory.recall $input }} => "Paris"
    /// </example>
    /// <param name="ask">The information to retrieve</param>
    /// <param name="context">Contains the 'collection' to search for information and 'relevance' score</param>
    [SKFunction("Recall a fact from the long term memory")]
    [SKFunctionName("Recall")]
    [SKFunctionInput(Description = "The information to retrieve")]
    [SKFunctionContextParameter(Name = CollectionParam, Description = "Memories collection where to search for information", DefaultValue = DefaultCollection)]
    [SKFunctionContextParameter(Name = RelevanceParam, Description = "The relevance score, from 0.0 to 1.0, where 1.0 means perfect match",
        DefaultValue = DefaultRelevance)]
    public async Task<string> RecallAsync(string ask, SKContext context)
    {
        var collection = context.Variables.ContainsKey(CollectionParam) ? context[CollectionParam] : DefaultCollection;
        Verify.NotEmpty(collection, "Memory collection not defined");

        var relevance = context.Variables.ContainsKey(RelevanceParam) ? context[RelevanceParam] : DefaultRelevance;
        if (string.IsNullOrWhiteSpace(relevance)) { relevance = DefaultRelevance; }

        context.Log.LogTrace("Searching memory for '{0}', collection '{1}', relevance '{2}'", ask, collection, relevance);

        // TODO: support locales, e.g. "0.7" and "0,7" must both work
        MemoryQueryResult? memory = await context.Memory
            .SearchAsync(collection, ask, limit: 1, minRelevanceScore: float.Parse(relevance, CultureInfo.InvariantCulture))
            .FirstOrDefaultAsync();

        if (memory == null)
        {
            context.Log.LogWarning("Memory not found in collection: {0}", collection);
        }
        else
        {
            context.Log.LogTrace("Memory found (collection: {0})", collection);
        }

        return memory != null ? memory.Text : string.Empty;
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
    [SKFunctionContextParameter(Name = CollectionParam, Description = "Memories collection where to save the information", DefaultValue = DefaultCollection)]
    [SKFunctionContextParameter(Name = KeyParam, Description = "The key to save the information")]
    public async Task SaveAsync(string text, SKContext context)
    {
        var collection = context.Variables.ContainsKey(CollectionParam) ? context[CollectionParam] : DefaultCollection;
        Verify.NotEmpty(collection, "Memory collection not defined");

        var key = context.Variables.ContainsKey(KeyParam) ? context[KeyParam] : string.Empty;
        Verify.NotEmpty(key, "Memory key not defined");

        context.Log.LogTrace("Saving memory to collection '{0}'", collection);

        await context.Memory.SaveInformationAsync(collection, text: text, id: key);
    }
}
