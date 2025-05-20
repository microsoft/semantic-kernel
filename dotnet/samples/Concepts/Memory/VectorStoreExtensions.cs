// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.AI;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Data;

namespace Memory;

/// <summary>
/// Extension methods for <see cref="VectorStore"/> which allow:
/// 1. Creating an instance of <see cref="VectorStoreCollection{TKey, TRecord}"/> from a list of strings.
/// </summary>
internal static class VectorStoreExtensions
{
    /// <summary>
    /// Delegate to create a record from a string.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    internal delegate TRecord CreateRecordFromString<TKey, TRecord>(string text, ReadOnlyMemory<float> vector) where TKey : notnull;

    /// <summary>
    /// Delegate to create a record from a <see cref="TextSearchResult"/>.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    internal delegate TRecord CreateRecordFromTextSearchResult<TKey, TRecord>(TextSearchResult searchResult, ReadOnlyMemory<float> vector) where TKey : notnull;

    /// <summary>
    /// Create a <see cref="VectorStoreCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Getting an instance of <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="vectorStore">Instance of <see cref="VectorStore"/> used to created the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="entries">A list of strings.</param>
    /// <param name="embeddingGenerator">An embedding generator.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    internal static async Task<VectorStoreCollection<TKey, TRecord>> CreateCollectionFromListAsync<TKey, TRecord>(
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

    /// <summary>
    /// Create a <see cref="VectorStoreCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Getting an instance of <see cref="VectorStoreCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="vectorStore">Instance of <see cref="VectorStore"/> used to created the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="searchResults">A list of <see cref="TextSearchResult" />s.</param>
    /// <param name="embeddingGenerator">An embedding generator service.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    internal static async Task<VectorStoreCollection<TKey, TRecord>> CreateCollectionFromTextSearchResultsAsync<TKey, TRecord>(
        this VectorStore vectorStore,
        string collectionName,
        IList<TextSearchResult> searchResults,
        IEmbeddingGenerator<string, Embedding<float>> embeddingGenerator,
        CreateRecordFromTextSearchResult<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : class
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        await collection.EnsureCollectionExistsAsync().ConfigureAwait(false);

        // Create records and generate embeddings for them.
        var tasks = searchResults.Select(searchResult => Task.Run(async () =>
        {
            var record = createRecord(searchResult, (await embeddingGenerator.GenerateAsync(searchResult.Value!).ConfigureAwait(false)).Vector);
            await collection.UpsertAsync(record).ConfigureAwait(false);
        }));
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return collection;
    }
}
