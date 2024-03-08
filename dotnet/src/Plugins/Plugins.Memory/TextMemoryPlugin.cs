// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
using System.Diagnostics.CodeAnalysis;
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Plugins.Memory;

/// <summary>
/// TextMemoryPlugin provides a plugin to save or recall information from the long or short term memory.
/// </summary>
[Experimental("SKEXP0003")]
public sealed class TextMemoryPlugin
{
    /// <summary>
    /// Name used to specify the input text.
    /// </summary>
    public const string InputParam = "input";
    /// <summary>
    /// Name used to specify which memory collection to use.
    /// </summary>
    public const string CollectionParam = "collection";

    /// <summary>
    /// Name used to specify memory search relevance score.
    /// </summary>
    public const string RelevanceParam = "relevance";

    /// <summary>
    /// Name used to specify a unique key associated with stored information.
    /// </summary>
    public const string KeyParam = "key";

    /// <summary>
    /// Name used to specify the number of memories to recall
    /// </summary>
    public const string LimitParam = "limit";

    private const string DefaultCollection = "generic";
    private const double DefaultRelevance = 0.0;
    private const int DefaultLimit = 1;

    private readonly ISemanticTextMemory _memory;
    private readonly ILogger _logger;

    /// <summary>
    /// Creates a new instance of the TextMemoryPlugin
    /// </summary>
    public TextMemoryPlugin(
        ISemanticTextMemory memory,
        ILoggerFactory? loggerFactory = null)
    {
        this._memory = memory;
        this._logger = loggerFactory?.CreateLogger(typeof(TextMemoryPlugin)) ?? NullLogger.Instance;
    }

    /// <summary>
    /// Key-based lookup for a specific memory
    /// </summary>
    /// <param name="key">The key associated with the memory to retrieve.</param>
    /// <param name="collection">Memories collection associated with the memory to retrieve</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Key-based lookup for a specific memory")]
    public async Task<string> RetrieveAsync(
        [Description("The key associated with the memory to retrieve")] string key,
        [Description("Memories collection associated with the memory to retrieve")] string? collection = DefaultCollection,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Recalling memory with key '{0}' from collection '{1}'", key, collection);
        }

        var memory = await this._memory.GetAsync(collection, key, cancellationToken: cancellationToken).ConfigureAwait(false);

        return memory?.Metadata.Text ?? string.Empty;
    }

    /// <summary>
    /// Semantic search and return up to N memories related to the input text
    /// </summary>
    /// <param name="input">The input text to find related memories for.</param>
    /// <param name="collection">Memories collection to search.</param>
    /// <param name="relevance">The relevance score, from 0.0 to 1.0, where 1.0 means perfect match.</param>
    /// <param name="limit">The maximum number of relevant memories to recall.</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Semantic search and return up to N memories related to the input text")]
    public async Task<string> RecallAsync(
        [Description("The input text to find related memories for")] string input,
        [Description("Memories collection to search")] string collection = DefaultCollection,
        [Description("The relevance score, from 0.0 to 1.0, where 1.0 means perfect match")] double? relevance = DefaultRelevance,
        [Description("The maximum number of relevant memories to recall")] int? limit = DefaultLimit,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(input);
        Verify.NotNullOrWhiteSpace(collection);

        relevance ??= DefaultRelevance;
        limit ??= DefaultLimit;

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Searching memories in collection '{0}', relevance '{1}'", collection, relevance);
        }

        // Search memory
        List<MemoryQueryResult> memories = await this._memory
            .SearchAsync(collection, input, limit.Value, relevance.Value, cancellationToken: cancellationToken)
            .ToListAsync(cancellationToken)
            .ConfigureAwait(false);

        if (memories.Count == 0)
        {
            if (this._logger.IsEnabled(LogLevel.Warning))
            {
                this._logger.LogWarning("Memories not found in collection: {0}", collection);
            }
            return string.Empty;
        }

        return limit == 1 ? memories[0].Metadata.Text : JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text));
    }

    /// <summary>
    /// Save information to semantic memory
    /// </summary>
    /// <param name="input">The information to save</param>
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="collection">Memories collection associated with the information to save</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Save information to semantic memory")]
    public async Task SaveAsync(
        [Description("The information to save")] string input,
        [Description("The key associated with the information to save")] string key,
        [Description("Memories collection associated with the information to save")] string collection = DefaultCollection,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Saving memory to collection '{0}'", collection);
        }

        await this._memory.SaveInformationAsync(collection, text: input, id: key, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove specific memory
    /// </summary>
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="collection">Memories collection associated with the information to save</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Remove specific memory")]
    public async Task RemoveAsync(
        [Description("The key associated with the information to save")] string key,
        [Description("Memories collection associated with the information to save")] string collection = DefaultCollection,
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Removing memory from collection '{0}'", collection);
        }

        await this._memory.RemoveAsync(collection, key, cancellationToken: cancellationToken).ConfigureAwait(false);
    }
}
