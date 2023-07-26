// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;

namespace Microsoft.SemanticKernel.Skills.Core;

/// <summary>
/// TextMemorySkill provides a skill to save or recall information from the long or short term memory.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("memory", new TextMemorySkill());
/// Examples:
/// SKContext.Variables["input"] = "what is the capital of France?"
/// {{memory.recall $input }} => "Paris"
/// </example>
public sealed class TextMemorySkill
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
    private const double DefaultRelevance = 0.0;
    private const int DefaultLimit = 1;

    private ISemanticTextMemory _memory;

    /// <summary>
    /// Creates a new instance of the TextMemorySkill
    /// </summary>
    public TextMemorySkill(ISemanticTextMemory memory)
    {
        this._memory = memory;
    }

    /// <summary>
    /// Key-based lookup for a specific memory
    /// </summary>
    /// <param name="collection">Memories collection associated with the memory to retrieve</param>
    /// <param name="key">The key associated with the memory to retrieve.</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    /// <example>
    /// SKContext.Variables[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.retrieve }}
    /// </example>
    [SKFunction, Description("Key-based lookup for a specific memory")]
    public async Task<string> RetrieveAsync(
        [SKName(CollectionParam), Description("Memories collection associated with the memory to retrieve"), DefaultValue(DefaultCollection)] string? collection,
        [SKName(KeyParam), Description("The key associated with the memory to retrieve")] string key,
        ILogger? logger,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);
        logger ??= NullLogger.Instance;

        logger.LogDebug("Recalling memory with key '{0}' from collection '{1}'", key, collection);

        var memory = await this._memory.GetAsync(collection, key, cancellationToken: cancellationToken).ConfigureAwait(false);

        return memory?.Metadata.Text ?? string.Empty;
    }

    /// <summary>
    /// Semantic search and return up to N memories related to the input text
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "what is the capital of France?"
    /// {{memory.recall $input }} => "Paris"
    /// </example>
    /// <param name="input">The input text to find related memories for.</param>
    /// <param name="collection">Memories collection to search.</param>
    /// <param name="relevance">The relevance score, from 0.0 to 1.0, where 1.0 means perfect match.</param>
    /// <param name="limit">The maximum number of relevant memories to recall.</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [SKFunction, Description("Semantic search and return up to N memories related to the input text")]
    public async Task<string> RecallAsync(
        [Description("The input text to find related memories for")] string input,
        [SKName(CollectionParam), Description("Memories collection to search"), DefaultValue(DefaultCollection)] string collection,
        [SKName(RelevanceParam), Description("The relevance score, from 0.0 to 1.0, where 1.0 means perfect match"), DefaultValue(DefaultRelevance)] double? relevance,
        [SKName(LimitParam), Description("The maximum number of relevant memories to recall"), DefaultValue(DefaultLimit)] int? limit,
        ILogger? logger,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        logger ??= NullLogger.Instance;
        relevance ??= DefaultRelevance;
        limit ??= DefaultLimit;

        logger.LogDebug("Searching memories in collection '{0}', relevance '{1}'", collection, relevance);

        // Search memory
        List<MemoryQueryResult> memories = await this._memory
            .SearchAsync(collection, input, limit.Value, relevance.Value, cancellationToken: cancellationToken)
            .ToListAsync(cancellationToken)
            .ConfigureAwait(false);

        if (memories.Count == 0)
        {
            logger.LogWarning("Memories not found in collection: {0}", collection);
            return string.Empty;
        }

        logger.LogTrace("Done looking for memories in collection '{0}')", collection);
        return limit == 1 ? memories[0].Metadata.Text : JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text));
    }

    /// <summary>
    /// Save information to semantic memory
    /// </summary>
    /// <example>
    /// SKContext.Variables["input"] = "the capital of France is Paris"
    /// SKContext.Variables[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.save $input }}
    /// </example>
    /// <param name="input">The information to save</param>
    /// <param name="collection">Memories collection associated with the information to save</param>
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [SKFunction, Description("Save information to semantic memory")]
    public async Task SaveAsync(
        [Description("The information to save")] string input,
        [SKName(CollectionParam), Description("Memories collection associated with the information to save"), DefaultValue(DefaultCollection)] string collection,
        [SKName(KeyParam), Description("The key associated with the information to save")] string key,
        ILogger? logger,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);
        logger ??= NullLogger.Instance;

        logger.LogDebug("Saving memory to collection '{0}'", collection);

        await this._memory.SaveInformationAsync(collection, text: input, id: key, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove specific memory
    /// </summary>
    /// <example>
    /// SKContext.Variables[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.remove }}
    /// </example>
    /// <param name="collection">Memories collection associated with the information to save</param>
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="logger">Application logger</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [SKFunction, Description("Remove specific memory")]
    public async Task RemoveAsync(
        [SKName(CollectionParam), Description("Memories collection associated with the information to save"), DefaultValue(DefaultCollection)] string collection,
        [SKName(KeyParam), Description("The key associated with the information to save")] string key,
        ILogger? logger,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);
        logger ??= NullLogger.Instance;

        logger.LogDebug("Removing memory from collection '{0}'", collection);

        await this._memory.RemoveAsync(collection, key, cancellationToken: cancellationToken).ConfigureAwait(false);
    }
}
