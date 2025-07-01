// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Redis;
using StackExchange.Redis;

namespace Memory.VectorStoreLangchainInterop;

/// <summary>
/// Contains a factory method that can be used to create a Redis vector store that is compatible with datasets ingested using Langchain.
/// </summary>
/// <remarks>
/// This class is used with the <see cref="VectorStore_Langchain_Interop"/> sample.
/// </remarks>
public static class RedisFactory
{
    /// <summary>
    /// Record definition that matches the storage format used by Langchain for Redis.
    /// </summary>
    private static readonly VectorStoreCollectionDefinition s_definition = new()
    {
        Properties = new List<VectorStoreProperty>
        {
            new VectorStoreKeyProperty("Key", typeof(string)),
            new VectorStoreDataProperty("Content", typeof(string)) { StorageName = "text" },
            new VectorStoreDataProperty("Source", typeof(string)) { StorageName = "source" },
            new VectorStoreVectorProperty("Embedding", typeof(ReadOnlyMemory<float>), 1536) { StorageName = "embedding" }
        }
    };

    /// <summary>
    /// Create a new Redis-backed <see cref="VectorStore"/> that can be used to read data that was ingested using Langchain.
    /// </summary>
    /// <param name="database">The redis database to read/write from.</param>
    /// <returns>The <see cref="VectorStore"/>.</returns>
    public static VectorStore CreateRedisLangchainInteropVectorStore(IDatabase database)
        => new RedisLangchainInteropVectorStore(new RedisVectorStore(database), database);

    private sealed class RedisLangchainInteropVectorStore(
        VectorStore innerStore,
        IDatabase database)
        : VectorStore
    {
        private readonly IDatabase _database = database;

        public override VectorStoreCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreCollectionDefinition? definition = null)
        {
            if (typeof(TKey) != typeof(string) || typeof(TRecord) != typeof(LangchainDocument<string>))
            {
                throw new NotSupportedException("This VectorStore is only usable with string keys and LangchainDocument<string> record types");
            }

            // Create a hash set collection, since Langchain uses redis hashes for storing records.
            // Also pass in our custom record definition that matches the schema used by Langchain
            // so that the default mapper can use the storage names in it, to map to the storage
            // scheme.
            return (new RedisHashSetCollection<TKey, TRecord>(
                _database,
                name,
                new()
                {
                    Definition = s_definition
                }) as VectorStoreCollection<TKey, TRecord>)!;
        }

        public override VectorStoreCollection<object, Dictionary<string, object?>> GetDynamicCollection(string name, VectorStoreCollectionDefinition? definition = null)
        {
            // Create a hash set collection, since Langchain uses redis hashes for storing records.
            // Also pass in our custom record definition that matches the schema used by Langchain
            // so that the default mapper can use the storage names in it, to map to the storage
            // scheme.
            return new RedisHashSetDynamicCollection(
                _database,
                name,
                new()
                {
                    Definition = s_definition
                });
        }

        public override object? GetService(Type serviceType, object? serviceKey = null) => innerStore.GetService(serviceType, serviceKey);

        public override IAsyncEnumerable<string> ListCollectionNamesAsync(CancellationToken cancellationToken = default) => innerStore.ListCollectionNamesAsync(cancellationToken);

        public override Task<bool> CollectionExistsAsync(string name, CancellationToken cancellationToken = default) => innerStore.CollectionExistsAsync(name, cancellationToken);

        public override Task EnsureCollectionDeletedAsync(string name, CancellationToken cancellationToken = default) => innerStore.EnsureCollectionDeletedAsync(name, cancellationToken);
    }
}
