// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;

namespace MCPServer;

/// <summary>
/// Extensions for vector stores.
/// </summary>
public static class VectorStoreExtensions
{
    /// <summary>
    /// Delegate to create a record from a string.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    public delegate TRecord CreateRecordFromString<TKey, TRecord>(string text, ReadOnlyMemory<float> vector) where TKey : notnull;

    /// <summary>
    /// Create a <see cref="VectorStoreCollection{TKey, TRecord}"/> from a list of strings by:
    /// </summary>
    /// <typeparam name="TKey">The data type of the record key.</typeparam>
    /// <typeparam name="TRecord">The data type of the record.</typeparam>
    /// <param name="vectorStore">The instance of <see cref="VectorStore"/> used to create the collection.</param>
    /// <param name="collectionName">The name of the collection.</param>
    /// <param name="entries">The list of strings to create records from.</param>
    /// <param name="embeddingGenerator">The text embedding generation service.</param>
    /// <param name="createRecord">The delegate which can create a record for each string and its embedding.</param>
    /// <returns>The created collection.</returns>
    public static async Task<VectorStoreCollection<TKey, TRecord>> CreateCollectionFromListAsync<TKey, TRecord>(
        this VectorStore vectorStore,
        string collectionName,
        string[] entries,
        IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator,
        CreateRecordFromString<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : class
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        await collection.EnsureCollectionExistsAsync().ConfigureAwait(false);

        // Create records and generate embeddings for them.
        var tasks = entries.Select(entry => Task.Run(async () =>
        {
            var record = createRecord(entry, (await embeddingGenerator.GenerateAsync(entry).ConfigureAwait(false)).Vector);
            await collection.UpsertAsync(record).ConfigureAwait(false);
        }));
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return collection;
    }
}
