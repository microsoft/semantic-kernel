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
using Microsoft.SemanticKernel.Memory.Storage;

namespace Microsoft.SemanticKernel.Skills.Memory.Sqlite;

/// <summary>
/// An implementation of <see cref="IDataStore{TValue}"/> backed by a SQLite database.
/// </summary>
/// <remarks>The data is saved to a database file, specified in the constructor.
/// The data persists between subsequent instances. Only one instance may access the file at a time.
/// The caller is responsible for deleting the file.</remarks>
/// <typeparam name="TValue">The type of data to be stored in this data store.</typeparam>
public class SqliteDataStore<TValue> : IDataStore<TValue>, IDisposable
{
    /// <summary>
    /// Connect a Sqlite database
    /// </summary>
    /// <param name="filename">Path to the database file. If file does not exist, it will be created.</param>
    /// <param name="cancel">Cancellation token</param>
    [SuppressMessage("Design", "CA1000:Do not declare static members on generic types",
        Justification = "Static factory method used to ensure successful connection.")]
    public static async Task<SqliteDataStore<TValue>> ConnectAsync(string filename,
        CancellationToken cancel = default)
    {
        SqliteConnection dbConnection = await Database.CreateConnectionAsync(filename, cancel);
        return new SqliteDataStore<TValue>(dbConnection);
    }

    /// <inheritdoc/>
    public IAsyncEnumerable<string> GetCollectionsAsync(CancellationToken cancel = default)
    {
        return this._dbConnection.GetCollectionsAsync(cancel);
    }

    /// <inheritdoc/>
    public async IAsyncEnumerable<DataEntry<TValue>> GetAllAsync(string collection,
        [EnumeratorCancellation] CancellationToken cancel = default)
    {
        await foreach (DatabaseEntry dbEntry in this._dbConnection.ReadAllAsync(collection, cancel))
        {
            yield return DataEntry.Create<TValue>(dbEntry.Key, dbEntry.Value, ParseTimestamp(dbEntry.Timestamp));
        }
    }

    /// <inheritdoc/>
    public async Task<DataEntry<TValue>?> GetAsync(string collection, string key, CancellationToken cancel = default)
    {
        DatabaseEntry? entry = await this._dbConnection.ReadAsync(collection, key, cancel);
        if (entry.HasValue)
        {
            DatabaseEntry dbEntry = entry.Value;
            return DataEntry.Create<TValue>(dbEntry.Key, dbEntry.Value, ParseTimestamp(dbEntry.Timestamp));
        }

        return null;
    }

    /// <inheritdoc/>
    public async Task<DataEntry<TValue>> PutAsync(string collection, DataEntry<TValue> data, CancellationToken cancel = default)
    {
        await this._dbConnection.InsertAsync(collection, data.Key, data.ValueString, ToTimestampString(data.Timestamp), cancel);
        return data;
    }

    /// <inheritdoc/>
    public Task RemoveAsync(string collection, string key, CancellationToken cancel = default)
    {
        return this._dbConnection.DeleteAsync(collection, key, cancel);
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
    private SqliteDataStore(SqliteConnection dbConnection)
    {
        this._dbConnection = dbConnection;
    }

    // TODO: never used
    private static string? ValueToString(TValue? value)
    {
        if (value != null)
        {
            if (typeof(TValue) == typeof(string))
            {
                return value.ToString();
            }

            return JsonSerializer.Serialize(value);
        }

        return null;
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
