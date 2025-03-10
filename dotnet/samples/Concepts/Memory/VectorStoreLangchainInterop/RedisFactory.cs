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
    private static readonly VectorStoreRecordDefinition s_recordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Content", typeof(string)) { StoragePropertyName = "text" },
            new VectorStoreRecordDataProperty("Source", typeof(string)) { StoragePropertyName = "source" },
            new VectorStoreRecordVectorProperty("Embedding", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "embedding", Dimensions = 1536 }
        }
    };

    /// <summary>
    /// Create a new Redis-backed <see cref="IVectorStore"/> that can be used to read data that was ingested using Langchain.
    /// </summary>
    /// <param name="database">The redis database to read/write from.</param>
    /// <returns>The <see cref="IVectorStore"/>.</returns>
    public static IVectorStore CreateRedisLangchainInteropVectorStore(IDatabase database)
        => new RedisLangchainInteropVectorStore(database);

    private sealed class RedisLangchainInteropVectorStore(IDatabase database)
        : RedisVectorStore(database)
    {
        private readonly IDatabase _database = database;

        public override IVectorStoreRecordCollection<TKey, TRecord> GetCollection<TKey, TRecord>(string name, VectorStoreRecordDefinition? vectorStoreRecordDefinition = null)
        {
            if (typeof(TKey) != typeof(string) || typeof(TRecord) != typeof(LangchainDocument<string>))
            {
                throw new NotSupportedException("This VectorStore is only usable with string keys and LangchainDocument<string> record types");
            }

            // Create a hash set collection, since Langchain uses redis hashes for storing records.
            // Also pass in our custom record definition that matches the schema used by Langchain
            // so that the default mapper can use the storage names in it, to map to the storage
            // scheme.
            return (new RedisHashSetVectorStoreRecordCollection<TRecord>(
                _database,
                name,
                new()
                {
                    VectorStoreRecordDefinition = s_recordDefinition
                }) as IVectorStoreRecordCollection<TKey, TRecord>)!;
        }
    }
}
