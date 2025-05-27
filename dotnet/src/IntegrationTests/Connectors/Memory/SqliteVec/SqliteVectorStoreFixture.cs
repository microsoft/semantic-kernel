// Copyright (c) Microsoft. All rights reserved.

using System;
using System.IO;
using Microsoft.SemanticKernel.Connectors.SqliteVec;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.SqliteVec;

public class SqliteVectorStoreFixture : IDisposable
{
    private readonly string _databasePath = Path.GetTempFileName();

    public string ConnectionString => $"Data Source={this._databasePath}";

    public SqliteCollection<TKey, TRecord> GetCollection<TKey, TRecord>(
        string collectionName,
        SqliteCollectionOptions? options = default)
        where TKey : notnull
        where TRecord : class
        => new(
            this.ConnectionString,
            collectionName,
            options);

    public SqliteDynamicCollection GetDynamicCollection(
        string collectionName,
        SqliteCollectionOptions options)
        => new(
            this.ConnectionString,
            collectionName,
            options);

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
