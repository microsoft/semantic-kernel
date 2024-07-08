// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using OpenAI;
using OpenAI.VectorStores;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// Fluent builder for creating a new <see cref="VectorStore"/>.
/// </summary>
/// <param name="config">Configuration for accessing the vector-store service.</param>
public sealed class OpenAIVectorStoreBuilder(OpenAIServiceConfiguration config)
{
    private string? _name;
    private FileChunkingStrategy? _chunkingStrategy;
    private VectorStoreExpirationPolicy? _expirationPolicy;
    private List<string>? _fileIds;
    private Dictionary<string, string>? _metadata;

    /// <summary>
    /// Added a file (by identifier) to the vector store.
    /// </summary>
    /// <param name="fileId"></param>
    public OpenAIVectorStoreBuilder AddFile(string fileId)
    {
        this._fileIds ??= [];
        this._fileIds.Add(fileId);

        return this;
    }

    /// <summary>
    /// Added files (by identifier) to the vector store.
    /// </summary>
    /// <param name="fileIds"></param>
    public OpenAIVectorStoreBuilder AddFiles(string[] fileIds)
    {
        this._fileIds ??= [];
        this._fileIds.AddRange(fileIds);

        return this;
    }

    /// <summary>
    /// Define the vector store chunking strategy (if not default).
    /// </summary>
    /// <param name="maxTokensPerChunk">The maximum number of tokens in each chunk. </param>
    /// <param name="overlappingTokenCount">The number of tokens that overlap between chunks.</param>
    public OpenAIVectorStoreBuilder WithChunkingStrategy(int maxTokensPerChunk, int overlappingTokenCount)
    {
        this._chunkingStrategy = FileChunkingStrategy.CreateStaticStrategy(maxTokensPerChunk, overlappingTokenCount);

        return this;
    }

    /// <summary>
    /// The number of days of from the last use until vector store will expire.
    /// </summary>
    /// <param name="duration">The duration (in days) from the last usage.</param>
    public OpenAIVectorStoreBuilder WithExpiration(TimeSpan duration)
    {
        this._expirationPolicy = new VectorStoreExpirationPolicy(VectorStoreExpirationAnchor.LastActiveAt, duration.Days);

        return this;
    }

    /// <summary>
    /// Adds a single key/value pair to the metadata.
    /// </summary>
    /// <param name="key">The metadata key</param>
    /// <param name="value">The metadata value</param>
    /// <remarks>
    /// The metadata is a set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </remarks>>
    public OpenAIVectorStoreBuilder WithMetadata(string key, string value)
    {
        this._metadata ??= [];

        this._metadata[key] = value;

        return this;
    }

    /// <summary>
    /// A set of up to 16 key/value pairs that can be attached to an agent, used for
    /// storing additional information about that object in a structured format.Keys
    /// may be up to 64 characters in length and values may be up to 512 characters in length.
    /// </summary>
    /// <param name="metadata">The metadata</param>
    public OpenAIVectorStoreBuilder WithMetadata(IDictionary<string, string> metadata)
    {
        this._metadata ??= [];

        foreach (KeyValuePair<string, string> item in this._metadata)
        {
            this._metadata[item.Key] = item.Value;
        }

        return this;
    }

    /// <summary>
    /// Defines the name of the vector store when not anonymous.
    /// </summary>
    /// <param name="name">The store name.</param>
    public OpenAIVectorStoreBuilder WithName(string name)
    {
        this._name = name;

        return this;
    }

    /// <summary>
    /// Creates a <see cref="VectorStore"/> as defined.
    /// </summary>
    /// <param name="cancellationToken">The <see cref="CancellationToken"/> to monitor for cancellation requests. The default is <see cref="CancellationToken.None"/>.</param>
    public async Task<VectorStore> CreateAsync(CancellationToken cancellationToken = default)
    {
        OpenAIClient openAIClient = OpenAIClientFactory.CreateClient(config);
        VectorStoreClient client = openAIClient.GetVectorStoreClient();

        VectorStoreCreationOptions options =
            new()
            {
                FileIds = this._fileIds,
                ChunkingStrategy = this._chunkingStrategy,
                ExpirationPolicy = this._expirationPolicy,
                Name = this._name,
            };

        if (this._metadata != null)
        {
            foreach (KeyValuePair<string, string> item in this._metadata)
            {
                options.Metadata.Add(item.Key, item.Value);
            }
        }

        VectorStore store = await client.CreateVectorStoreAsync(options, cancellationToken).ConfigureAwait(false);

        return store;
    }
}
