// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.SqlServer;
using Testcontainers.MsSql;
using VectorData.ConformanceTests.Support;

namespace SqlServer.ConformanceTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class SqlServerTestStore : TestStore
{
    public static SqlServerTestStore Instance { get; } = new();

    private static readonly MsSqlContainer s_container = new MsSqlBuilder()
        .WithImage("mcr.microsoft.com/mssql/server:2025-latest")
        .Build();

    private string? _connectionString;
    private bool _useExternalInstance;

    public string ConnectionString => this._connectionString ?? throw new InvalidOperationException("Not initialized");

    public SqlServerVectorStore GetVectorStore(SqlServerVectorStoreOptions options)
        => new(this.ConnectionString, options);

    public override string DefaultDistanceFunction => DistanceFunction.CosineDistance;

    private SqlServerTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        if (SqlServerTestEnvironment.IsConnectionStringDefined)
        {
            this._connectionString = SqlServerTestEnvironment.ConnectionString!;
            this._useExternalInstance = true;
        }
        else
        {
            // Use testcontainer if no external connection string is provided
            await s_container.StartAsync();
            this._connectionString = s_container.GetConnectionString();
            this._useExternalInstance = false;
        }

        this.DefaultVectorStore = new SqlServerVectorStore(this._connectionString);
    }

    protected override async Task StopAsync()
    {
        // Only stop the container if we started it
        if (!this._useExternalInstance)
        {
            await s_container.StopAsync();
        }
    }
}
