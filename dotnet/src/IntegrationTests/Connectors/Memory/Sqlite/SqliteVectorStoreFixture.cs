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

    public SqliteConnection Connection { get; }

    public SqliteVectorStoreFixture()
    {
        this.Connection = new SqliteConnection("Data Source=:memory:");
    }

    public SqliteVectorStoreRecordCollection<TRecord> GetCollection<TRecord>(
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        return new SqliteVectorStoreRecordCollection<TRecord>(
            this.Connection,
            collectionName,
            options);
    }

    public Task DisposeAsync()
    {
        return Task.CompletedTask;
    }

    public async Task InitializeAsync()
    {
        await this.Connection.OpenAsync();

        this.Connection.LoadExtension(VectorSearchExtensionName);
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
            this.Connection.Dispose();
        }
    }
}
