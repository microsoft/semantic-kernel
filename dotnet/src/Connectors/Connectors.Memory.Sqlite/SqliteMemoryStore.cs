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
public class SqliteMemoryStore : IMemoryStore, IDisposable
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
        await memoryStore._dbConnection.OpenAsync(cancel);
        await memoryStore._dbConnector.CreateTableAsync(memoryStore._dbConnection, cancel);
        return memoryStore;
    }

    /// <inheritdoc/>
    public async Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        await this._dbConnector.CreateCollectionAsync(this._dbConnection, collectionName, cancel);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        return await this._dbConnector.DoesCollectionExistsAsync(this._dbConnection, collectionName, cancel);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> GetCollectionsAsync([EnumeratorCancellation] CancellationToken cancel = default)
    {
        await foreach (var collection in this._dbConnector.GetCollectionsAsync(this._dbConnection, cancel))
        {
            yield return collection;
        }
    }

    /// <inheritdoc/>
    public async Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        await this._dbConnector.DeleteCollectionAsync(this._dbConnection, collectionName, cancel);
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        return await this.InternalUpsertAsync(this._dbConnection, collectionName, record, cancel);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var record in records)
        {
            yield return await this.InternalUpsertAsync(this._dbConnection, collectionName, record, cancel);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, bool withEmbedding = false, CancellationToken cancel = default)
    {
        return await this.InternalGetAsync(this._dbConnection, collectionName, key, withEmbedding, cancel);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, bool withEmbeddings = false,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var key in keys)
        {
            var result = await this.InternalGetAsync(this._dbConnection, collectionName, key, withEmbeddings, cancel);
            if (result != null)
            {
                yield return result;
            }
            else
            {
                yield break;
            }
        }
    }

    /// <inheritdoc/>
    public async Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        await this._dbConnector.DeleteAsync(this._dbConnection, collectionName, key, cancel);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        await Task.WhenAll(keys.Select(k => this._dbConnector.DeleteAsync(this._dbConnection, collectionName, k, cancel)));
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

    /// <inheritdoc/>
    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    #region protected ================================================================================

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._dbConnection.Close();
                SqliteConnection.ClearAllPools();
                this._dbConnection.Dispose();
            }

            this._disposedValue = true;
        }
    }

    #endregion

    #region private ================================================================================

    private readonly Database _dbConnector;
    private readonly SqliteConnection _dbConnection;
    private bool _disposedValue;

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="filename">Sqlite db filename.</param>
    private SqliteMemoryStore(string filename)
    {
        this._dbConnector = new Database();
        this._dbConnection = new SqliteConnection($@"Data Source={filename};");
        this._disposedValue = false;
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
        // delete empty entry in the database if it exists (see CreateCollection)
        await this._dbConnector.DeleteEmptyAsync(this._dbConnection, collectionName, cancel);

        await foreach (DatabaseEntry dbEntry in this._dbConnector.ReadAllAsync(this._dbConnection, collectionName, cancel))
        {
            Embedding<float>? vector = JsonSerializer.Deserialize<Embedding<float>>(dbEntry.EmbeddingString);

            var record = MemoryRecord.FromJsonMetadata(dbEntry.MetadataString, vector, dbEntry.Key, ParseTimestamp(dbEntry.Timestamp));

            yield return record;
        }
    }

    private async Task<string> InternalUpsertAsync(SqliteConnection connection, string collectionName, MemoryRecord record, CancellationToken cancel)
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

        return record.Key;
    }

    private async Task<MemoryRecord?> InternalGetAsync(SqliteConnection connection, string collectionName, string key, bool withEmbedding, CancellationToken cancel)
    {
        DatabaseEntry? entry = await this._dbConnector.ReadAsync(connection, collectionName, key, cancel);

        if (entry.HasValue)
        {
            if (withEmbedding)
            {
                return MemoryRecord.FromJsonMetadata(
                    json: entry.Value.MetadataString,
                    JsonSerializer.Deserialize<Embedding<float>>(entry.Value.EmbeddingString),
                    entry.Value.Key,
                    ParseTimestamp(entry.Value.Timestamp));
            }
            else
            {
                return MemoryRecord.FromJsonMetadata(
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

    #endregion
}
