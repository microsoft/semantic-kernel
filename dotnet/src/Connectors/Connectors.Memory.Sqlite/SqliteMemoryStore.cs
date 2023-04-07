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
        SqliteConnection dbConnection = await Database.CreateConnectionAsync(filename, cancel);
        return new SqliteMemoryStore(dbConnection);
    }

    /// <inheritdoc/>
    public Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        return this._dbConnection.CreateCollectionAsync(collectionName, cancel);
    }

    /// <inheritdoc/>
    public async Task<bool> DoesCollectionExistAsync(string collectionName, CancellationToken cancel = default)
    {
        return await this._dbConnection.DoesCollectionExistsAsync(collectionName, cancel);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._dbConnection.GetCollectionsAsync(cancel);
    }

    /// <inheritdoc/>
    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        return this._dbConnection.DeleteCollectionAsync(collectionName, cancel);
    }

    /// <inheritdoc/>
    public async Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        record.Key = record.Metadata.Id;

        // Update
        await this._dbConnection.UpdateAsync(
            collection: collectionName,
            key: record.Key,
            value: JsonSerializer.Serialize(record),
            timestamp: ToTimestampString(record.Timestamp),
            cancel: cancel);

        // Insert if entry does not exists
        await this._dbConnection.InsertOrIgnoreAsync(
            collection: collectionName,
            key: record.Key,
            value: JsonSerializer.Serialize(record),
            timestamp: ToTimestampString(record.Timestamp),
            cancel: cancel);

        return record.Key;
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> records,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var r in records)
        {
            yield return await this.UpsertAsync(collectionName, r, cancel);
        }
    }

    /// <inheritdoc/>
    public async Task<MemoryRecord?> GetAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        DatabaseEntry? entry = await this._dbConnection.ReadAsync(collectionName, key, cancel);

        if (entry.HasValue)
        {
            return JsonSerializer.Deserialize<MemoryRecord>(entry.Value.ValueString);
        }
        else
        {
            return null;
        }
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        foreach (var key in keys)
        {
            var record = await this.GetAsync(collectionName, key, cancel);

            if (record != null)
            {
                yield return record;
            }
        }
    }

    /// <inheritdoc/>
    public Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        return this._dbConnection.DeleteAsync(collectionName, key, cancel);
    }

    /// <inheritdoc/>
    public async Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        await Task.WhenAll(keys.Select(k => this.RemoveAsync(collectionName, k, cancel)));
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(
        string collectionName,
        Embedding<float> embedding,
        int limit,
        double minRelevanceScore = 0,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        if (limit <= 0)
        {
            yield break;
        }

        var collectionMemories = new List<MemoryRecord>();
        TopNCollection<MemoryRecord> embeddings = new(limit);

        await foreach (var entry in this.GetAllAsync(collectionName, cancel))
        {
            if (entry != null)
            {
                double similarity = embedding
                    .AsReadOnlySpan()
                    .CosineSimilarity(entry.Embedding.AsReadOnlySpan());
                if (similarity >= minRelevanceScore)
                {
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
    public async Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0,
        CancellationToken cancel = default)
    {
        return await this.GetNearestMatchesAsync(
            collectionName: collectionName,
            embedding: embedding,
            limit: 1,
            minRelevanceScore: minRelevanceScore,
            cancel: cancel).FirstOrDefaultAsync(cancellationToken: cancel);
    }

    /// <summary>
    /// Performs application-defined tasks associated with freeing, releasing, or resetting unmanaged resources.
    /// </summary>
    public void Dispose()
    {
        // Do not change this code. Put cleanup code in 'Dispose(bool disposing)' method
        this.Dispose(disposing: true);
        GC.SuppressFinalize(this);
    }

    #region protected ================================================================================

    protected virtual void Dispose(bool disposing)
    {
        if (!this._disposedValue)
        {
            if (disposing)
            {
                this._dbConnection.Dispose();
            }

            this._disposedValue = true;
        }
    }

    #endregion

    #region private ================================================================================

    private readonly SqliteConnection _dbConnection;
    private bool _disposedValue;

    /// <summary>
    /// Constructor
    /// </summary>
    /// <param name="dbConnection">DB connection</param>
    private SqliteMemoryStore(SqliteConnection dbConnection)
    {
        this._dbConnection = dbConnection;
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
        await this._dbConnection.DeleteEmptyAsync(collectionName, cancel);

        await foreach (DatabaseEntry dbEntry in this._dbConnection.ReadAllAsync(collectionName, cancel))
        {
            var record = JsonSerializer.Deserialize<MemoryRecord>(dbEntry.ValueString);
            if (record != null)
            {
                yield return record;
            }
        }
    }

    #endregion
}
