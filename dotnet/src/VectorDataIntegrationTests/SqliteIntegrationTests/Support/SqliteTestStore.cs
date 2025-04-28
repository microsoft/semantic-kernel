// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using VectorDataSpecificationTests.Support;

namespace SqliteIntegrationTests.Support;

internal sealed class SqliteTestStore : TestStore
{
    private string? _databasePath;

    private string? _connectionString;
    public string ConnectionString => this._connectionString ?? throw new InvalidOperationException("Not initialized");

    public static SqliteTestStore Instance { get; } = new();

    private SqliteVectorStore? _defaultVectorStore;
    public override IVectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Call InitializeAsync() first");

    public override string DefaultDistanceFunction => Microsoft.Extensions.VectorData.DistanceFunction.CosineDistance;

    public SqliteVectorStore GetVectorStore(SqliteVectorStoreOptions options)
        => new(this.ConnectionString, options);

    private SqliteTestStore()
    {
    }

    protected override Task StartAsync()
    {
        this._databasePath = Path.GetTempFileName();
        this._connectionString = $"Data Source={this._databasePath}";
        this._defaultVectorStore = new SqliteVectorStore(this._connectionString);
        return Task.CompletedTask;
    }

    protected override Task StopAsync()
    {
        File.Delete(this._databasePath!);
        this._databasePath = null;
        return Task.CompletedTask;
    }
}
