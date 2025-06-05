// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using VectorData.ConformanceTests.Support;

namespace SqlServer.ConformanceTests.Support;

public sealed class SqlServerTestStore : TestStore
{
    private string? _connectionString;
    public string ConnectionString => this._connectionString ?? throw new InvalidOperationException("Not initialized");

    public static readonly SqlServerTestStore Instance = new();

    public SqlServerVectorStore GetVectorStore(SqlServerVectorStoreOptions options)
        => new(this.ConnectionString, options);

    public override string DefaultDistanceFunction => DistanceFunction.CosineDistance;

    protected override Task StartAsync()
    {
        this._connectionString = SqlServerTestEnvironment.ConnectionString;

        if (string.IsNullOrWhiteSpace(this._connectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the SqlServer:ConnectionString environment variable");
        }

        this.DefaultVectorStore = new SqlServerVectorStore(this._connectionString);

        return Task.CompletedTask;
    }
}
