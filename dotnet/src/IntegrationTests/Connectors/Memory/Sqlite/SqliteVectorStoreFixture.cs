// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

public class SqliteVectorStoreFixture : IDisposable
{
    private readonly string _databasePath = Path.GetTempFileName();

    public string ConnectionString => $"Data Source={this._databasePath}";

    public SqliteVectorStoreRecordCollection<TRecord> GetCollection<TRecord>(
        string collectionName,
        SqliteVectorStoreRecordCollectionOptions<TRecord>? options = default)
    {
        return new SqliteVectorStoreRecordCollection<TRecord>(
            this.ConnectionString,
            collectionName,
            options);
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
            File.Delete(this._databasePath);
        }
    }
}
