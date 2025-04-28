// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.CompilerServices;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using NRedisStack.RedisStackCommands;
using StackExchange.Redis;

namespace Microsoft.SemanticKernel.Connectors.Redis;

/// <summary>
/// Class for accessing the list of collections in a Redis vector store.
/// </summary>
/// <remarks>
/// This class can be used with collections of any schema type, but requires you to provide schema information when getting a collection.
/// </remarks>
public sealed class RedisVectorStore : IVectorStore
{
    /// <summary>Metadata about vector store.</summary>
    private readonly VectorStoreMetadata _metadata;

    /// <summary>The redis database to read/write indices from.</summary>
    private readonly IDatabase _database;

    /// <summary>Optional configuration options for this class.</summary>
    private readonly RedisVectorStoreOptions _options;

    /// <summary>A general purpose definition that can be used to construct a collection when needing to proxy schema agnostic operations.</summary>
    private static readonly VectorStoreRecordDefinition s_generalPurposeDefinition = new() { Properties = [new VectorStoreRecordKeyProperty("Key", typeof(string))] };

    /// <summary>
    /// Initializes a new instance of the <see cref="RedisVectorStore"/> class.
    /// </summary>
    /// <param name="database">The redis database to read/write indices from.</param>
    /// <param name="options">Optional configuration options for this class.</param>
    public RedisVectorStore(IDatabase database, RedisVectorStoreOptions? options = default)
    {
        Verify.NotNull(database);

        this._database = database;
        this._options = options ?? new RedisVectorStoreOptions();

        this._metadata = new()
        {
            VectorStoreSystemName = RedisConstants.VectorStoreSystemName,
            VectorStoreName = database.Database.ToString()
        };
    }

    /// <inheritdoc />
    public IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        where TKey : notnull
        where TRecord : notnull
    {
#pragma warning disable CS0618 // IRedisVectorStoreRecordCollectionFactory is obsolete
        if (this._options.VectorStoreCollectionFactory is not null)
        {
            return this._options.VectorStoreCollectionFactory.CreateVectorStoreRecordCollection<TKey, TRecord>(this._database, name, vectorStoreRecordDefinition);
        }
#pragma warning restore CS0618

        if (this._options.StorageType == RedisStorageType.HashSet)
        {
            var recordCollection = new RedisHashSetVectorStoreRecordCollection<TKey, TRecord>(this._database, name, new RedisHashSetVectorStoreRecordCollectionOptions<TRecord>()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            }) as IVectorStoreRecordCollection<TKey, TRecord>;
            return recordCollection!;
        }
        else
        {
            var recordCollection = new RedisJsonVectorStoreRecordCollection<TKey, TRecord>(this._database, name, new RedisJsonVectorStoreRecordCollectionOptions<TRecord>()
            {
                VectorStoreRecordDefinition = vectorStoreRecordDefinition,
                EmbeddingGenerator = this._options.EmbeddingGenerator
            }) as IVectorStoreRecordCollection<TKey, TRecord>;
            return recordCollection!;
        }
    }

    /// <inheritdoc />
    public async IAsyncEnumerable<string> ListCollectionNamesAsync([EnumeratorCancellation] CancellationToken cancellationToken = default)
    {
        const string OperationName = "";
        RedisResult[] listResult;

        try
        {
            listResult = await this._database.FT()._ListAsync().ConfigureAwait(false);
        }
        catch (RedisException ex)
        {
            throw new VectorStoreOperationException("Call to vector store failed.", ex)
            {
                VectorStoreSystemName = RedisConstants.VectorStoreSystemName,
                VectorStoreName = this._metadata.VectorStoreName,
                OperationName = OperationName
            };
        }

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
    public Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.CollectionExistsAsync(cancellationToken);
    }

    /// <inheritdoc />
    public Task DeleteCollectionAsync(string name, CancellationToken cancellationToken = default)
    {
        var collection = this.GetCollection<object, Dictionary<string, object>>(name, s_generalPurposeDefinition);
        return collection.DeleteCollectionAsync(cancellationToken);
    }

    /// <inheritdoc />
    public object? GetService(Type serviceType, object? serviceKey = null)
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
