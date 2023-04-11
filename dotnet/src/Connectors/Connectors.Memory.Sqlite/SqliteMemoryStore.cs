// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Linq;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.AI.Embeddings.VectorOperations;
using Microsoft.SemanticKernel.Memory;
using Microsoft.SemanticKernel.Memory.Collections;

namespace Microsoft.SemanticKernel.Connectors.Memory.Sqlite;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a SQLite database.
/// </summary>
/// <remarks>The data is saved to a database file, specified in the constructor.
/// The data persists between subsequent instances. Only one instance may access the file at a time.
/// The caller is responsible for deleting the file.</remarks>
public class SqliteMemoryStore : IMemoryStore
{
    /// <summary>
    /// Connect a Sqlite database
    /// </summary>
    /// <param name="filename">Path to the database file. If file does not exist, it will be created.</param>
    /// <param name="cancel">Cancellation token</param>
    [SuppressMessage("Design", "CA1000:Do not declare static members on generic types",
        Justification = "Static factory method used to ensure successful connection.")]
    public static async Task<SqliteMemoryStore> ConnectAsync(string filename,
        CancellationToken cancel = default)
    {
        var memoryStore = new SqliteMemoryStore(filename);
        await memoryStore._dbConnector.CreateConnectionAsync(memoryStore._dbConnectionString, cancel);
        return memoryStore;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            await this._dbConnector.CreateCollectionAsync(connection, collectionName, cancel);
        }
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            return await this._dbConnector.DoesCollectionExistsAsync(connection, collectionName, cancel);
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            await foreach (var collection in this._dbConnector.GetCollectionsAsync(connection, cancel))
            {
                yield return collection;
            }
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            await this._dbConnector.DeleteCollectionAsync(connection, collectionName, cancel);
        }
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            record.Key = record.Metadata.Id;

            // Update
            await this._dbConnector.UpdateAsync(
                conn: connection,
                collection: collectionName,
                key: record.Key,
                metadata: record.GetSerializedMetadata(),
                embedding: JsonSerializer.Serialize(record.Embedding),
                timestamp: ToTimestampString(record.Timestamp),
                cancel: cancel);

            // Insert if entry does not exists
            await this._dbConnector.InsertOrIgnoreAsync(
                conn: connection,
                collection: collectionName,
                key: record.Key,
                metadata: record.GetSerializedMetadata(),
                embedding: JsonSerializer.Serialize(record.Embedding),
                timestamp: ToTimestampString(record.Timestamp),
                cancel: cancel);

            return record.Key;
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            foreach (var record in records)
            {
                record.Key = record.Metadata.Id;

                // Update
                await this._dbConnector.UpdateAsync(
                    conn: connection,
                    collection: collectionName,
                    key: record.Key,
                    metadata: record.GetSerializedMetadata(),
                    embedding: JsonSerializer.Serialize(record.Embedding),
                    timestamp: ToTimestampString(record.Timestamp),
                    cancel: cancel);

                // Insert if entry does not exists
                await this._dbConnector.InsertOrIgnoreAsync(
                    conn: connection,
                    collection: collectionName,
                    key: record.Key,
                    metadata: record.GetSerializedMetadata(),
                    embedding: JsonSerializer.Serialize(record.Embedding),
                    timestamp: ToTimestampString(record.Timestamp),
                    cancel: cancel);

                yield return record.Key;
            }
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            DatabaseEntry? entry = await this._dbConnector.ReadAsync(connection, collectionName, key, cancel);

            if (entry.HasValue)
            {
                if (withEmbedding)
                {
                    return MemoryRecord.FromJson(
                        json: entry.Value.MetadataString,
                        JsonSerializer.Deserialize<Embedding<float>>(entry.Value.EmbeddingString),
                        entry.Value.Key,
                        ParseTimestamp(entry.Value.Timestamp));
                }
                else
                {
                    return MemoryRecord.FromJson(
                        json: entry.Value.MetadataString,
                        Embedding<float>.Empty,
                        entry.Value.Key,
                        ParseTimestamp(entry.Value.Timestamp));
                }
            }
            else
            {
                return null;
            }
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            foreach (var key in keys)
            {
                DatabaseEntry? entry = await this._dbConnector.ReadAsync(connection, collectionName, key, cancel);

                if (entry.HasValue)
                {
                    if (withEmbeddings)
                    {
                        yield return MemoryRecord.FromJson(
                            json: entry.Value.MetadataString,
                            JsonSerializer.Deserialize<Embedding<float>>(entry.Value.EmbeddingString),
                            entry.Value.Key,
                            ParseTimestamp(entry.Value.Timestamp));
                    }
                    else
                    {
                        yield return MemoryRecord.FromJson(
                            json: entry.Value.MetadataString,
                            Embedding<float>.Empty,
                            entry.Value.Key,
                            ParseTimestamp(entry.Value.Timestamp));
                    }
                }
                else
                {
                    yield break;
                }
            }
        }
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            await this._dbConnector.DeleteAsync(connection, collectionName, key, cancel);
        }
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            await Task.WhenAll(keys.Select(k => this._dbConnector.DeleteAsync(connection, collectionName, k, cancel)));
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (limit <= 0)
        {
            yield break;
        }

        var collectionMemories = new List<MemoryRecord>();
        TopNCollection<MemoryRecord> embeddings = new(limit);

        await foreach (var record in this.GetAllAsync(collectionName, cancel))
        {
            if (record != null)
            {
                double similarity = embedding
                    .AsReadOnlySpan()
                    .CosineSimilarity(record.Embedding.AsReadOnlySpan());
                if (similarity >= minRelevanceScore)
                {
                    var entry = withEmbeddings ? record : MemoryRecord.FromMetadata(record.Metadata, Embedding<float>.Empty, record.Key, record.Timestamp);
                    embeddings.Add(new(entry, similarity));
                }
            }
        }

        embeddings.SortByScore();

        foreach (var item in embeddings)
        {
            yield return (item.Value, item.Score.Value);
        }
    }

    /// <inheritdoc/>
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, bool withEmbedding = false,
        CancellationToken cancel = default)
    {
        return await this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            limit: 1,
            minRelevanceScore: minRelevanceScore,
            withEmbeddings: withEmbedding,
            cancel: cancel).FirstOrDefaultAsync(cancellationToken: cancel);
    }

    #region private ================================================================================

    private readonly string _dbConnectionString;
    private readonly Database _dbConnector;

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="filename">Sqlite db filename.</param>
    private SqliteMemoryStore(string filename)
    {
        this._dbConnectionString = $@"Data Source={filename};Pooling=false;";
        this._dbConnector = new Database();
    }

    private static string? ToTimestampString(DateTimeOffset? timestamp)
    {
        return timestamp?.ToString("u", CultureInfo.InvariantCulture);
    }

    private static DateTimeOffset? ParseTimestamp(string? str)
    {
        if (!string.IsNullOrEmpty(str)
            && DateTimeOffset.TryParse(str, CultureInfo.InvariantCulture, DateTimeStyles.AssumeUniversal, out DateTimeOffset timestamp))
        {
            return timestamp;
        }

        return null;
    }

    private async IAsyncEnumerable<MemoryRecord> GetAllAsync(string collectionName, [EnumeratorCancellation] CancellationToken cancel = default)
    {
        await using (var connection = new SqliteConnection(this._dbConnectionString))
        {
            await connection.OpenAsync(cancel);
            // delete empty entry in the database if it exists (see CreateCollection)
            await this._dbConnector.DeleteEmptyAsync(connection, collectionName, cancel);

            await foreach (DatabaseEntry dbEntry in this._dbConnector.ReadAllAsync(connection, collectionName, cancel))
            {
                Embedding<float>? vector = JsonSerializer.Deserialize<Embedding<float>>(dbEntry.EmbeddingString);

                var record = MemoryRecord.FromJson(dbEntry.MetadataString, vector, dbEntry.Key, ParseTimestamp(dbEntry.Timestamp));

                yield return record;
            }
        }
    }

    #endregion
}
