// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;

namespace Microsoft.SemanticKernel.Connectors.InMemory;

/// <summary>
/// Extension methods for <see cref="InMemoryVectorStore"/> which allow:
/// 1. Serializing an instance of <see cref="InMemoryVectorStoreRecordCollection{TKey, TRecord}"/> to a stream.
/// 2. Deserializing an instance of <see cref="InMemoryVectorStoreRecordCollection{TKey, TRecord}"/> from a stream.
/// </summary>
public static class InMemoryVectorStoreExtensions
{
    /// <summary>
    /// Serialize a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> to a stream as JSON.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    /// <param name="vectorStore">Instance of <see cref="InMemoryVectorStore"/> used to retrieve the collection.</param>
    /// <param name="collectionName">The collection name.</param>
    /// <param name="stream">The stream to write the serialized JSON to.</param>
    /// <param name="jsonSerializerOptions">The JSON serializer options to use.</param>
    public static async Task SerializeCollectionAsJsonAsync<TKey, TRecord>(
        this InMemoryVectorStore vectorStore,
        string collectionName,
        Stream stream,
        JsonSerializerOptions? jsonSerializerOptions = null)
        where TKey : notnull
        where TRecord : notnull
    {
        // Get collection and verify that it exists.
        var collection = vectorStore.GetCollection<TKey, TRecord>(collectionName);
        var exists = await collection.CollectionExistsAsync().ConfigureAwait(false);
        if (!exists)
        {
            throw new InvalidOperationException($"Collection '{collectionName}' does not exist.");
        }

        var inMemoryCollection = collection as InMemoryVectorStoreRecordCollection<TKey, TRecord>;
        var records = inMemoryCollection!.GetCollectionDictionary();
        InMemoryRecordCollection<object, object> recordCollection = new(collectionName, records);

        await JsonSerializer.SerializeAsync(stream, recordCollection, jsonSerializerOptions).ConfigureAwait(false);
    }

    /// <summary>
    /// Deserialize a <see cref="IVectorStoreRecordCollection{TKey, TRecord}"/> to a stream as JSON.
    /// </summary>
    /// <typeparam name="TKey">Type of the record key.</typeparam>
    /// <typeparam name="TRecord">Type of the record.</typeparam>
    /// <param name="vectorStore">Instance of <see cref="InMemoryVectorStore"/> used to retrieve the collection.</param>
    /// <param name="stream">The stream to read the serialized JSON from.</param>
    public static async Task<IVectorStoreRecordCollection<TKey, TRecord>?> DeserializeCollectionFromJsonAsync<TKey, TRecord>(
        this InMemoryVectorStore vectorStore,
        Stream stream)
        where TKey : notnull
        where TRecord : notnull
    {
        IVectorStoreRecordCollection<TKey, TRecord>? collection = null;

        using (StreamReader streamReader = new(stream))
        {
            string result = streamReader.ReadToEnd();
            var recordCollection = JsonSerializer.Deserialize<InMemoryRecordCollection<TKey, TRecord>>(result);
            if (recordCollection is null)
            {
                throw new InvalidOperationException("Stream does not contain valid record collection JSON.");
            }

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

        return collection;
    }

    #region private
    /// <summary>Model class used when storing a <see cref="InMemoryVectorStoreRecordCollection{TKey, TRecord}" />.</summary>
    private sealed class InMemoryRecordCollection<TKey, TRecord>(string name, IDictionary<TKey, TRecord> records)
        where TKey : notnull
    {
        public string Name { get; init; } = name;
        public IDictionary<TKey, TRecord> Records { get; init; } = records;
    }
    #endregion

}
