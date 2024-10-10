// Copyright (c) Microsoft. All rights reserved.

using System.Collections.Generic;
using System.ComponentModel;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using System.Diagnostics.CodeAnalysis;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
using System.Diagnostics.CodeAnalysis;
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
using System.Diagnostics.CodeAnalysis;
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
using System.Diagnostics.CodeAnalysis;
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
using System.Linq;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.Logging.Abstractions;
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
using Microsoft.SemanticKernel.Memory;
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> origin/main
using Microsoft.SemanticKernel.Memory;
=======
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
using Microsoft.SemanticKernel.Memory;
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
using Microsoft.SemanticKernel.Diagnostics;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.SkillDefinition;
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

namespace Microsoft.SemanticKernel.Plugins.Memory;

/// <summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
/// TextMemoryPlugin provides a plugin to save or recall information from the long or short term memory.
/// </summary>
[Experimental("SKEXP0001")]
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
/// TextMemoryPlugin provides a plugin to save or recall information from the long or short term memory.
/// </summary>
[Experimental("SKEXP0001")]
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
public sealed class TextMemoryPlugin
{
    /// <summary>
    /// Name used to specify the input text.
    /// </summary>
    public const string InputParam = "input";
    /// <summary>
    /// Name used to specify which memory collection to use.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> origin/main
=======
=======
>>>>>>> Stashed changes
public sealed class TextMemoryPlugin
{
    /// <summary>
    /// Name used to specify the input text.
    /// </summary>
    public const string InputParam = "input";
    /// <summary>
    /// Name used to specify which memory collection to use.
=======
/// TextMemorySkill provides a skill to save or recall information from the long or short term memory.
/// </summary>
/// <example>
/// Usage: kernel.ImportSkill("memory", new TextMemorySkill());
/// Examples:
/// SKContext.Variables["input"] = "what is the capital of France?"
/// {{memory.recall $input }} => "Paris"
/// </example>
public sealed class TextMemoryPlugin
{
    /// <summary>
    /// Name of the context variable used to specify which memory collection to use.
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    /// </summary>
    public const string CollectionParam = "collection";

    /// <summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// Name used to specify memory search relevance score.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    /// Name used to specify memory search relevance score.
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
    /// Name used to specify memory search relevance score.
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// Name used to specify memory search relevance score.
=======
    /// Name of the context variable used to specify memory search relevance score.
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    /// </summary>
    public const string RelevanceParam = "relevance";

    /// <summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// Name used to specify a unique key associated with stored information.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    /// Name used to specify a unique key associated with stored information.
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
    /// Name used to specify a unique key associated with stored information.
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// Name used to specify a unique key associated with stored information.
=======
    /// Name of the context variable used to specify a unique key associated with stored information.
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    /// </summary>
    public const string KeyParam = "key";

    /// <summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    /// Name used to specify the number of memories to recall
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    /// Name used to specify the number of memories to recall
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
    /// Name used to specify the number of memories to recall
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    /// Name used to specify the number of memories to recall
=======
    /// Name of the context variable used to specify the number of memories to recall
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    /// </summary>
    public const string LimitParam = "limit";

    private const string DefaultCollection = "generic";
    private const double DefaultRelevance = 0.0;
    private const int DefaultLimit = 1;

<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
    private readonly ISemanticTextMemory _memory;
    private readonly ILogger _logger;
    private readonly JsonSerializerOptions? _jsonSerializerOptions;

    /// <summary>
    /// Initializes a new instance of the <see cref="TextMemoryPlugin"/> class.
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
    /// </summary>
    /// <param name="memory">The <see cref="ISemanticTextMemory"/> instance to use for retrieving and saving memories to and from storage.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="jsonSerializerOptions">An optional <see cref="JsonSerializerOptions"/> to use when turning multiple memories into json text. If null, <see cref="JsonSerializerOptions.Default"/> is used.</param>
    public TextMemoryPlugin(
        ISemanticTextMemory memory,
        ILoggerFactory? loggerFactory = null,
        JsonSerializerOptions? jsonSerializerOptions = null)
    {
        this._memory = memory;
        this._logger = loggerFactory?.CreateLogger(typeof(TextMemoryPlugin)) ?? NullLogger.Instance;
        this._jsonSerializerOptions = jsonSerializerOptions ?? JsonSerializerOptions.Default;
=======
    private ISemanticTextMemory _memory;

    /// <summary>
    /// Creates a new instance of the TextMemorySkill
>>>>>>> origin/main
    /// </summary>
    /// <param name="memory">The <see cref="ISemanticTextMemory"/> instance to use for retrieving and saving memories to and from storage.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="jsonSerializerOptions">An optional <see cref="JsonSerializerOptions"/> to use when turning multiple memories into json text. If null, <see cref="JsonSerializerOptions.Default"/> is used.</param>
    public TextMemoryPlugin(
        ISemanticTextMemory memory,
        ILoggerFactory? loggerFactory = null,
        JsonSerializerOptions? jsonSerializerOptions = null)
    {
        this._memory = memory;
<<<<<<< Updated upstream
<<<<<<< head
        this._logger = loggerFactory?.CreateLogger(typeof(TextMemoryPlugin)) ?? NullLogger.Instance;
        this._jsonSerializerOptions = jsonSerializerOptions ?? JsonSerializerOptions.Default;
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    private ISemanticTextMemory _memory;

    /// <summary>
    /// Creates a new instance of the TextMemorySkill
>>>>>>> origin/main
    /// </summary>
    /// <param name="memory">The <see cref="ISemanticTextMemory"/> instance to use for retrieving and saving memories to and from storage.</param>
    /// <param name="loggerFactory">The <see cref="ILoggerFactory"/> to use for logging. If null, no logging will be performed.</param>
    /// <param name="jsonSerializerOptions">An optional <see cref="JsonSerializerOptions"/> to use when turning multiple memories into json text. If null, <see cref="JsonSerializerOptions.Default"/> is used.</param>
    public TextMemoryPlugin(
        ISemanticTextMemory memory,
        ILoggerFactory? loggerFactory = null,
        JsonSerializerOptions? jsonSerializerOptions = null)
    {
        this._memory = memory;
=======
>>>>>>> Stashed changes
<<<<<<< main
        this._logger = loggerFactory?.CreateLogger(typeof(TextMemoryPlugin)) ?? NullLogger.Instance;
        this._jsonSerializerOptions = jsonSerializerOptions ?? JsonSerializerOptions.Default;
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Key-based lookup for a specific memory
    /// </summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
=======
<<<<<<< main
>>>>>>> Stashed changes
    /// <param name="key">The key associated with the memory to retrieve.</param>
=======
<<<<<<< HEAD
    /// <param name="key">The key associated with the memory to retrieve.</param>
    /// <param name="collection">Memories collection associated with the memory to retrieve</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Key-based lookup for a specific memory")]
    public async Task<string> RetrieveAsync(
        [Description("The key associated with the memory to retrieve")] string key,
        [Description("Memories collection associated with the memory to retrieve")] string? collection = DefaultCollection,
=======
>>>>>>> origin/main
=======
<<<<<<< main
    /// <param name="key">The key associated with the memory to retrieve.</param>
>>>>>>> Stashed changes
    /// <param name="collection">Memories collection associated with the memory to retrieve</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Key-based lookup for a specific memory")]
    public async Task<string> RetrieveAsync(
        [Description("The key associated with the memory to retrieve")] string key,
        [Description("Memories collection associated with the memory to retrieve")] string? collection = DefaultCollection,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
    /// <param name="key">The key associated with the memory to retrieve.</param>
<<<<<<< head
=======
=======
<<<<<<< HEAD
    /// <param name="key">The key associated with the memory to retrieve.</param>
>>>>>>> Stashed changes
    /// <param name="collection">Memories collection associated with the memory to retrieve</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Key-based lookup for a specific memory")]
    public async Task<string> RetrieveAsync(
        [Description("The key associated with the memory to retrieve")] string key,
        [Description("Memories collection associated with the memory to retrieve")] string? collection = DefaultCollection,
=======
    /// <param name="collection">Memories collection associated with the memory to retrieve</param>
    /// <param name="key">The key associated with the memory to retrieve.</param>
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
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
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Recalling memory with key '{0}' from collection '{1}'", key, collection);
        }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        logger ??= NullLogger.Instance;

<<<<<<< main
        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Recalling memory with key '{0}' from collection '{1}'", key, collection);
        }
=======
        logger.LogDebug("Recalling memory with key '{0}' from collection '{1}'", key, collection);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Recalling memory with key '{0}' from collection '{1}'", key, collection);
        }
=======
        logger ??= NullLogger.Instance;

        logger.LogDebug("Recalling memory with key '{0}' from collection '{1}'", key, collection);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

        var memory = await this._memory.GetAsync(collection, key, cancellationToken: cancellationToken).ConfigureAwait(false);

        return memory?.Metadata.Text ?? string.Empty;
    }

    /// <summary>
    /// Semantic search and return up to N memories related to the input text
    /// </summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
<<<<<<< main
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    /// <example>
    /// SKContext.Variables["input"] = "what is the capital of France?"
    /// {{memory.recall $input }} => "Paris"
    /// </example>
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    /// <param name="input">The input text to find related memories for.</param>
    /// <param name="collection">Memories collection to search.</param>
    /// <param name="relevance">The relevance score, from 0.0 to 1.0, where 1.0 means perfect match.</param>
    /// <param name="limit">The maximum number of relevant memories to recall.</param>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
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
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
>>>>>>> origin/main
=======
=======
<<<<<<< main
=======
=======
>>>>>>> Stashed changes
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
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main

        // Search memory
        List<MemoryQueryResult> memories = await this._memory
            .SearchAsync(collection, input, limit.Value, relevance.Value, cancellationToken: cancellationToken)
            .ToListAsync(cancellationToken)
            .ConfigureAwait(false);

        if (memories.Count == 0)
        {
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
            if (this._logger.IsEnabled(LogLevel.Warning))
            {
                this._logger.LogWarning("Memories not found in collection: {0}", collection);
            }
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
            return string.Empty;
        }

        return limit == 1 ? memories[0].Metadata.Text : JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text), this._jsonSerializerOptions);
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
=======
=======
            logger.LogWarning("Memories not found in collection: {0}", collection);
            return string.Empty;
        }

        logger.LogTrace("Done looking for memories in collection '{0}')", collection);
        return limit == 1 ? memories[0].Metadata.Text : JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text));
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            return string.Empty;
        }

        return limit == 1 ? memories[0].Metadata.Text : JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text), this._jsonSerializerOptions);
=======
            logger.LogWarning("Memories not found in collection: {0}", collection);
            return string.Empty;
        }

        logger.LogTrace("Done looking for memories in collection '{0}')", collection);
        return limit == 1 ? memories[0].Metadata.Text : JsonSerializer.Serialize(memories.Select(x => x.Metadata.Text));
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    }

    /// <summary>
    /// Save information to semantic memory
    /// </summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
<<<<<<< main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
    /// <param name="input">The information to save</param>
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="collection">Memories collection associated with the information to save</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Save information to semantic memory")]
    public async Task SaveAsync(
        [Description("The information to save")] string input,
        [Description("The key associated with the information to save")] string key,
        [Description("Memories collection associated with the information to save")] string collection = DefaultCollection,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
    /// <example>
    /// SKContext.Variables["input"] = "the capital of France is Paris"
    /// SKContext.Variables[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.save $input }}
    /// </example>
>>>>>>> origin/main
    /// <param name="input">The information to save</param>
    /// <param name="key">The key associated with the information to save</param>
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
<<<<<<< main
    /// <param name="collection">Memories collection associated with the information to save</param>
=======
    /// <param name="logger">Application logger</param>
>>>>>>> origin/main
<<<<<<< Updated upstream
=======
    /// <param name="logger">Application logger</param>
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [SKFunction, Description("Save information to semantic memory")]
    public async Task SaveAsync(
        [Description("The information to save")] string input,
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
<<<<<<< main
        [Description("The key associated with the information to save")] string key,
        [Description("Memories collection associated with the information to save")] string collection = DefaultCollection,
=======
<<<<<<< Updated upstream
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        [SKName(CollectionParam), Description("Memories collection associated with the information to save"), DefaultValue(DefaultCollection)] string collection,
        [SKName(KeyParam), Description("The key associated with the information to save")] string key,
        ILogger? logger,
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
<<<<<<< HEAD
>>>>>>> Stashed changes

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Saving memory to collection '{0}'", collection);
        }
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        logger ??= NullLogger.Instance;

<<<<<<< main
        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Saving memory to collection '{0}'", collection);
        }
=======
        logger.LogDebug("Saving memory to collection '{0}'", collection);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
        logger ??= NullLogger.Instance;

        logger.LogDebug("Saving memory to collection '{0}'", collection);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
=======
>>>>>>> Stashed changes

        await this._memory.SaveInformationAsync(collection, text: input, id: key, cancellationToken: cancellationToken).ConfigureAwait(false);
    }

    /// <summary>
    /// Remove specific memory
    /// </summary>
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< main
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="collection">Memories collection associated with the information to save</param>
=======
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="collection">Memories collection associated with the information to save</param>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [KernelFunction, Description("Remove specific memory")]
    public async Task RemoveAsync(
        [Description("The key associated with the information to save")] string key,
        [Description("Memories collection associated with the information to save")] string collection = DefaultCollection,
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
=======
    /// <example>
    /// SKContext.Variables[TextMemorySkill.KeyParam] = "countryInfo1"
    /// {{memory.remove }}
    /// </example>
    /// <param name="collection">Memories collection associated with the information to save</param>
    /// <param name="key">The key associated with the information to save</param>
    /// <param name="logger">Application logger</param>
<<<<<<< Updated upstream
<<<<<<< head
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [SKFunction, Description("Remove specific memory")]
    public async Task RemoveAsync(
<<<<<<< main
        [Description("The key associated with the information to save")] string key,
        [Description("Memories collection associated with the information to save")] string collection = DefaultCollection,
=======
<<<<<<< Updated upstream
=======
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    [SKFunction, Description("Remove specific memory")]
    public async Task RemoveAsync(
>>>>>>> origin/main
=======
>>>>>>> Stashed changes
        [SKName(CollectionParam), Description("Memories collection associated with the information to save"), DefaultValue(DefaultCollection)] string collection,
        [SKName(KeyParam), Description("The key associated with the information to save")] string key,
        ILogger? logger,
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
<<<<<<< Updated upstream
<<<<<<< head
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> origin/main
        CancellationToken cancellationToken = default)
    {
        Verify.NotNullOrWhiteSpace(collection);
        Verify.NotNullOrWhiteSpace(key);
<<<<<<< Updated upstream
<<<<<<< head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD

        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Removing memory from collection '{0}'", collection);
        }
=======
        logger ??= NullLogger.Instance;

<<<<<<< main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Removing memory from collection '{0}'", collection);
        }
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        logger.LogDebug("Removing memory from collection '{0}'", collection);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD

=======
>>>>>>> Stashed changes
        if (this._logger.IsEnabled(LogLevel.Debug))
        {
            this._logger.LogDebug("Removing memory from collection '{0}'", collection);
        }
=======
<<<<<<< Updated upstream
        logger ??= NullLogger.Instance;

=======
>>>>>>> Stashed changes
        logger.LogDebug("Removing memory from collection '{0}'", collection);
>>>>>>> f5c8882d73157409ff27fb857a432fda2fa6c2a3
>>>>>>> origin/main

        await this._memory.RemoveAsync(collection, key, cancellationToken: cancellationToken).ConfigureAwait(false);
    }
}
