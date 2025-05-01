// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Extension methods for <see cref="IVectorStore"/> which allow:
/// 1. Creating an instance of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings.
/// </summary>
public static class VectorStoreExtensions
{
    /// <summary>
    /// Delegate to create a record from a string.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    public delegate TRecord CreateRecordFromString<TKey, TRecord>(int index, string text, ReadOnlyMemory<float> vector) where TKey : notnull;

    /// <summary>
    /// Delegate to create a record from a <see cref="TextSearchResult"/>.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    public delegate TRecord CreateRecordFromTextSearchResult<TKey, TRecord>(TextSearchResult searchResult, ReadOnlyMemory<float> vector) where TKey : notnull;

    /// <summary>
    /// Create a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Getting an instance of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="vectorStore">Instance of <see cref="IVectorStore"/> used to created the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="entries">A list of strings.</param>
    /// <param name="embeddingGenerationService">A text embedding generation service.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    internal static async Task<IVectorStoreRecordCollection<TKey, TRecord>> CreateCollectionFromListAsync<TKey, TRecord>(
        this IVectorStore vectorStore,
        string collectionName,
        string[] entries,
        ITextEmbeddingGenerationService embeddingGenerationService,
        CreateRecordFromString<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : notnull
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        await collection.CreateCollectionIfNotExistsAsync().ConfigureAwait(false);

        // Create records and generate embeddings for them.
        var tasks = entries.Select((entry, i) => Task.Run(async () =>
        {
            var record = createRecord(i, entry, await embeddingGenerationService.GenerateEmbeddingAsync(entry).ConfigureAwait(false));
            await collection.UpsertAsync(record).ConfigureAwait(false);
        }));
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return collection;
    }

    /// <summary>
    /// Create a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Getting an instance of <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="vectorStore">Instance of <see cref="IVectorStore"/> used to created the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="searchResults">A list of <see cref="TextSearchResult" />s.</param>
    /// <param name="embeddingGenerationService">A text embedding generation service.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    internal static async Task<IVectorStoreRecordCollection<TKey, TRecord>> CreateCollectionFromTextSearchResultsAsync<TKey, TRecord>(
        this IVectorStore vectorStore,
        string collectionName,
        IList<TextSearchResult> searchResults,
        ITextEmbeddingGenerationService embeddingGenerationService,
        CreateRecordFromTextSearchResult<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : notnull
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        await collection.CreateCollectionIfNotExistsAsync().ConfigureAwait(false);

        // Create records and generate embeddings for them.
        var tasks = searchResults.Select(searchResult => Task.Run(async () =>
        {
            var record = createRecord(searchResult, await embeddingGenerationService.GenerateEmbeddingAsync(searchResult.Value!).ConfigureAwait(false));
            await collection.UpsertAsync(record).ConfigureAwait(false);
        }));
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return collection;
    }
}
