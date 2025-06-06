// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.SqliteVec;
using VectorData.ConformanceTests.Support;

namespace SqliteVec.ConformanceTests.Support;

internal sealed class SqliteTestStore : TestStore
{
    private string? _databasePath;

    private string? _connectionString;
    public string ConnectionString => this._connectionString ?? throw new InvalidOperationException("Not initialized");

    public static SqliteTestStore Instance { get; } = new();

    public override string DefaultDistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    public SqliteVectorStore GetVectorStore(SqliteVectorStoreOptions options)
        => new(this.ConnectionString, options);

    private SqliteTestStore()
    {
    }

    protected override Task StartAsync()
    {
        this._databasePath = Path.GetTempFileName();
        this._connectionString = $"Data Source={this._databasePath};Pooling=false";
        this.DefaultVectorStore = new SqliteVectorStore(this._connectionString);
        return Task.CompletedTask;
    }

    protected override Task StopAsync()
    {
        File.Delete(this._databasePath!);
        this._databasePath = null;
        return Task.CompletedTask;
    }
}
