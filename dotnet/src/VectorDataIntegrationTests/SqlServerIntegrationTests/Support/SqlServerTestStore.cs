// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using VectorDataSpecificationTests.Support;

namespace SqlServerIntegrationTests.Support;

public sealed class SqlServerTestStore : TestStore
{
    private string? _connectionString;
    public string ConnectionString => this._connectionString ?? throw new InvalidOperationException("Not initialized");

    public static readonly SqlServerTestStore Instance = new();

    public override IVectorStore DefaultVectorStore
        => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public SqlServerVectorStore GetVectorStore(SqlServerVectorStoreOptions options)
        => new(this.ConnectionString, options);

    public override string DefaultDistanceFunction => DistanceFunction.CosineDistance;

    private SqlServerVectorStore? _defaultVectorStore;

    protected override Task StartAsync()
    {
        this._connectionString = SqlServerTestEnvironment.ConnectionString;

        if (string.IsNullOrWhiteSpace(this._connectionString))
        {
            throw new InvalidOperationException("Connection string is not configured, set the SqlServer:ConnectionString environment variable");
        }

        this._defaultVectorStore = new(this._connectionString);

        return Task.CompletedTask;
    }
}
