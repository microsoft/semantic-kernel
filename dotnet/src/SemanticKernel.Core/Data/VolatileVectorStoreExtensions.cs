// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Embeddings;

namespace Microsoft.SemanticKernel.Data;

/// <summary>
/// Extension methods for <see cref="VolatileVectorStore"/> which allow:
/// 1. Creating an instance of <see cref="VolatileVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings.
/// 2. Serializing an instance of <see cref="VolatileVectorStoreRecordCollection{TKey, TRecord}"/> to a stream.
/// 3. Deserializing an instance of <see cref="VolatileVectorStoreRecordCollection{TKey, TRecord}"/> from a stream.
/// </summary>
public static class VolatileVectorStoreExtensions
{
    /// <summary>
    /// Delegate to create a record.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    public delegate TRecord CreateRecord<TKey, TRecord>(string text, ReadOnlyMemory<float> vector) where TKey : notnull where TRecord : class;

    /// <summary>
    /// Create a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> from a list of strings by:
    /// 1. Creating an instance of <see cref="VolatileVectorStoreRecordCollection{TKey, TRecord}"/>
    /// 2. Generating embeddings for each string.
    /// 3. Creating a record with a valid key for each string and it's embedding.
    /// 4. Insert the records into the collection.
    /// </summary>
    /// <param name="vectorStore">Instance of <see cref="VolatileVectorStore"/> used to created the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="entries">A list of strings.</param>
    /// <param name="embeddingGenerationService">A text embedding generation service.</param>
    /// <param name="createRecord">A delegate which can create a record with a valid key for each string and it's embedding.</param>
    public static async Task<IVectorStoreRecordCollection<TKey, TRecord>> CreateCollectionFromListAsync<TKey, TRecord>(
        this VolatileVectorStore vectorStore,
        string collectionName,
        string[] entries,
        ITextEmbeddingGenerationService embeddingGenerationService,
        CreateRecord<TKey, TRecord> createRecord)
        where TKey : notnull
        where TRecord : class
    {
        // Get and create collection if it doesn't exist.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        await collection.CreateCollectionIfNotExistsAsync().ConfigureAwait(false);

        // Create records and generate embeddings for them.
        var tasks = entries.Select(entry => Task.Run(async () =>
        {
            var record = createRecord(entry, await embeddingGenerationService.GenerateEmbeddingAsync(entry).ConfigureAwait(false));
            await collection.UpsertAsync(record).ConfigureAwait(false);
        }));
        await Task.WhenAll(tasks).ConfigureAwait(false);

        return collection;
    }

    /// <summary>
    /// Serialize a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> to a stream as JSON.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    /// <param name="vectorStore">Instance of <see cref="VolatileVectorStore"/> used to retrieve the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="stream">The stream to write the serialized JSON to.</param>
    /// <param name="jsonSerializerOptions">The JSON serializer options to use.</param>
    public static async Task SerializeAsJsonAsync<TKey, TRecord>(
        this VolatileVectorStore vectorStore,
        string collectionName,
        Stream stream,
        JsonSerializerOptions? jsonSerializerOptions = null)
        where TKey : notnull
        where TRecord : class
    {
        // Get collection and verify that it exists.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        var exists = await collection.CollectionExistsAsync().ConfigureAwait(false);
        if (!exists)
        {
            throw new InvalidOperationException($"Collection '{collectionName}' does not exist.");
        }

        var volatileCollection = collection as VolatileVectorStoreRecordCollection<TKey, TRecord>;
        var records = volatileCollection!.GetCollectionDictionary();
        if (records is null)
        {
            throw new InvalidOperationException($"Collection '{collectionName}' is not the correct type.");
        }
        VolatileRecordCollection<object, object> recordCollection = new(collectionName, records);

        jsonSerializerOptions ??= s_jsonSerializerOptions;
        await JsonSerializer.SerializeAsync(stream, recordCollection, jsonSerializerOptions).ConfigureAwait(false);
    }

    /// <summary>
    /// Deserialize a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> to a stream as JSON.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    /// <param name="vectorStore">Instance of <see cref="VolatileVectorStore"/> used to retrieve the collection.</param>
    /// <param name="stream">The stream to read the serialized JSON from.</param>
    public static async Task<IVectorStoreRecordCollection<TKey, TRecord>?> DeserializeFromJsonAsync<TKey, TRecord>(
        this VolatileVectorStore vectorStore,
        Stream stream)
        where TKey : notnull
        where TRecord : class
    {
        IVectorStoreRecordCollection<TKey, TRecord>? collection = null;

        using (StreamReader streamReader = new(stream))
        {
            string result = streamReader.ReadToEnd();
            var recordCollection = JsonSerializer.Deserialize<VolatileRecordCollection<TKey, TRecord>>(result);
            if (recordCollection is not null)
            {
                // Get and create collection if it doesn't exist.
                collection = vectorStore.GetCollection<TKey, TRecord>(recordCollection.Name);
                await collection.CreateCollectionIfNotExistsAsync().ConfigureAwait(false);

                // Upsert records.
                var tasks = recordCollection.Records.Values.Select(record => Task.Run(async () =>
                {
                    await collection.UpsertAsync(record).ConfigureAwait(false);
                }));
                await Task.WhenAll(tasks).ConfigureAwait(false);
            }
        }

        return collection;
    }

    #region private
    /// <summary>JSON serialization configuration for readable output.</summary>
    private static readonly JsonSerializerOptions s_jsonSerializerOptions = new() { WriteIndented = true };

    /// <summary>Model class used when storing a <see cref="VolatileVectorStoreRecordCollection{TKey, TRecord}" />.</summary>
    private sealed class VolatileRecordCollection<TKey, TRecord>(string name, IDictionary<TKey, TRecord> records)
        where TKey : notnull
        where TRecord : class
    {
        public string Name { get; init; } = name;
        public IDictionary<TKey, TRecord> Records { get; init; } = records;
    }
    #endregion

}
