// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Diagnostics.CodeAnalysis;
using System.Globalization;
using System.Runtime.CompilerServices;
using System.Text.Json;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.AI.Embeddings;
using Microsoft.SemanticKernel.Memory;

namespace Microsoft.SemanticKernel.Skills.Memory.Sqlite;

/// <summary>
/// An implementation of <see cref="IMemoryStore"/> backed by a SQLite database.
/// </summary>
/// <remarks>The data is saved to a database file, specified in the constructor.
/// The data persists between subsequent instances. Only one instance may access the file at a time.
/// The caller is responsible for deleting the file.</remarks>
/// <typeparam name="TValue">The type of data to be stored in this data store.</typeparam>
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

    public Task CreateCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public Task DeleteCollectionAsync(string collectionName, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public Task<string> UpsertAsync(string collectionName, MemoryRecord record, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<string> UpsertBatchAsync(string collectionName, IEnumerable<MemoryRecord> record, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public Task<MemoryRecord?> GetAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<MemoryRecord> GetBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public Task RemoveAsync(string collectionName, string key, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public Task RemoveBatchAsync(string collectionName, IEnumerable<string> keys, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public IAsyncEnumerable<(MemoryRecord, double)> GetNearestMatchesAsync(string collectionName, Embedding<float> embedding, int limit, double minRelevanceScore = 0, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
    }

    public Task<(MemoryRecord, double)?> GetNearestMatchAsync(string collectionName, Embedding<float> embedding, double minRelevanceScore = 0, CancellationToken cancel = default)
    {
        throw new NotImplementedException();
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

    #endregion
}
