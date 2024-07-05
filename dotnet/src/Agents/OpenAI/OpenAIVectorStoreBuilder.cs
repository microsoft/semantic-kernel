// Copyright (c) Microsoft. All rights reserved.
using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using OpenAI;
using OpenAI.VectorStores;

namespace Microsoft.SemanticKernel.Agents.OpenAI;

/// <summary>
/// %%%
/// </summary>
public sealed class OpenAIVectorStoreBuilder(OpenAIConfiguration config)
{
    private string? _name;
    private FileChunkingStrategy? _chunkingStrategy;
    private VectorStoreExpirationPolicy? _expirationPolicy;
    private List<string>? _fileIds;
    private Dictionary<string, string>? _metadata;

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="fileId"></param>
    public OpenAIVectorStoreBuilder AddFile(string fileId)
    {
        this._fileIds ??= [];
        this._fileIds.Add(fileId);

        return this;
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="fileIds"></param>
    public OpenAIVectorStoreBuilder AddFile(string[] fileIds)
    {
        this._fileIds ??= [];
        this._fileIds.AddRange(fileIds);

        return this;
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="maxTokensPerChunk"></param>
    /// <param name="overlappingTokenCount"></param>
    public OpenAIVectorStoreBuilder WithChunkingStrategy(int maxTokensPerChunk, int overlappingTokenCount)
    {
        this._chunkingStrategy = FileChunkingStrategy.CreateStaticStrategy(maxTokensPerChunk, overlappingTokenCount);

        return this;
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="duration"></param>
    public OpenAIVectorStoreBuilder WithExpiration(TimeSpan duration)
    {
        this._expirationPolicy = new VectorStoreExpirationPolicy(VectorStoreExpirationAnchor.LastActiveAt, duration.Days);

        return this;
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="key"></param>
    /// <param name="value"></param>
    /// <returns></returns>
    public OpenAIVectorStoreBuilder WithMetadata(string key, string value)
    {
        this._metadata ??= [];

        this._metadata[key] = value;

        return this;
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="metadata"></param>
    /// <returns></returns>
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
    /// %%%
    /// </summary>
    /// <param name="name"></param>
    /// <returns></returns>
    public OpenAIVectorStoreBuilder WithName(string name)
    {
        this._name = name;

        return this;
    }

    /// <summary>
    /// %%%
    /// </summary>
    /// <param name="cancellationToken"></param>
    /// <returns></returns>
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
