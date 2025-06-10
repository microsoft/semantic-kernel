// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Diagnostics.CodeAnalysis;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using NRedisStack.RedisStackCommands;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for accessing the list of collections in a Redis vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class RedisVectorStore : VectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>The redis database to read/write indices from.</summary>
    private readonly IDatabase _database;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreCollectionDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreKeyProperty("Key", typeof(string))] };

    /// <summary>The way in which data should be stored in redis..</summary>
    private readonly RedisStorageType? _storageType;

    private readonly IEmbeddingGenerator? _embeddingGenerator;

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisVectorStore"/> class.
    /// </summary>
    /// <param name="database">The redis database to read/write indices from.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    [RequiresUnreferencedCode("The Redis provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Redis provider is currently incompatible with NativeAOT.")]
    public RedisVectorStore(IDatabase database, RedisVectorStoreOptions? options = default)
    {
        Verify.NotNull(database);

        this._database = database;

        options ??= RedisVectorStoreOptions.Default;
        this._storageType = options.StorageType;
        this._embeddingGenerator = options.EmbeddingGenerator;

        this._metadata = new()
        {
            VectorStoreSystemName = RedisConstants.VectorStoreSystemName,
            VectorStoreName = database.Database.ToString()
        };
    }

    /// <inheritdoc />
    // TODO: The provider uses unsafe JSON serialization in many places, #11963
    [RequiresUnreferencedCode("The Weaviate provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Weaviate provider is currently incompatible with NativeAOT.")]
    public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
    {
        if (typeof(TRecord) == typeof(Dictionary<string, object?>))
        {
            throw new ArgumentException(VectorDataStrings.GetCollectionWithDictionaryNotSupported);
        }

        return this._storageType switch
        {
            RedisStorageType.HashSet => new RedisHashSetCollection<TKey, TRecord>(this._database, name, new RedisHashSetCollectionOptions()
            {
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator
            }),

            RedisStorageType.Json => new RedisJsonCollection<TKey, TRecord>(this._database, name, new RedisJsonCollectionOptions()
            {
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator
            }),

            _ => throw new UnreachableException()
        };
    }

    /// <inheritdoc />
    // TODO: The provider uses unsafe JSON serialization in many places, #11963
    [RequiresUnreferencedCode("The Redis provider is currently incompatible with trimming.")]
    [RequiresDynamicCode("The Redis provider is currently incompatible with NativeAOT.")]
    public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition definition)
        => this._storageType switch
        {
            RedisStorageType.HashSet => new RedisHashSetDynamicCollection(this._database, name, new RedisHashSetCollectionOptions()
            {
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator
            }),

            RedisStorageType.Json => new RedisJsonDynamicCollection(this._database, name, new RedisJsonCollectionOptions()
            {
                Definition = definition,
                EmbeddingGenerator = this._embeddingGenerator
            }),

            _ => throw new UnreachableException()
        };

    /// <inheritdoc />
    public override async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "FT._LIST";

        var listResult = await VectorStoreErrorHandler.RunOperationAsync<RedisResult[], RedisException>(
            this._metadata,
            OperationName,
            () => this._database.FT()._ListAsync()).ConfigureAwait(false);

        foreach (var item in listResult)
        {
            var name = item.ToString();
            if (name != null)
            {
                yield return name;
            }
        }
    }

    /// <inheritdoc />
    public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetDynamicCollection(name, s_generalPurposeDefinition);
        return collection.EnsureCollectionDeletedAsync(cancellationToken);
    }

    /// <inheritdoc />
    public override object? GetService(Type serviceType, object? serviceKey = null)
    {
        Verify.NotNull(serviceType);

        return
            serviceKey is not null ? null :
            serviceType == typeof(VectorStoreMetadata) ? this._metadata :
            serviceType == typeof(IDatabase) ? this._metadata :
            serviceType.IsInstanceOfType(this) ? this :
            null;
    }
}
