// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

public class SqliteVectorStoreFixture : IAsyncLifetime, IDisposable
{
    /// <summary>
    /// SQLite extension name for vector search.
    /// More information here: <see href="https://github.com/asg017/sqlite-vec"/>.
    /// </summary>
    private const string VectorSearchExtensionName = "vec0";

    private readonly SqliteConnection _connection;

    public SqliteVectorStoreFixture()
    {
        this._connection = new SqliteConnection("Data Source=:memory:");
    }

    public SqliteVectorStoreRecordCollection<TRecord> GetCollection<TRecord>(
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
        where TRecord : class
    {
        return new SqliteVectorStoreRecordCollection<TRecord>(
            this._connection,
            collectionName,
            VectorSearchExtensionName,
            options);
    }

    public Task DisposeAsync()
    {
        return Task.CompletedTask;
    }

    public async Task InitializeAsync()
    {
        await this._connection.OpenAsync();

        this._connection.LoadExtension(VectorSearchExtensionName);
    }

    public void Dispose()
    {
        this.Dispose(true);
        GC.SuppressFinalize(this);
    }

    protected virtual void Dispose(bool disposing)
    {
        if (disposing)
        {
            this._connection.Dispose();
        }
    }
}
