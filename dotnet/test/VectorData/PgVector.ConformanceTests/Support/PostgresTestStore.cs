// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.PgVector;
using Npgsql;
using Testcontainers.PostgreSql;
using VectorData.ConformanceTests.Support;

namespace PgVector.ConformanceTests.Support;

#pragma warning disable CA1001 // Type owns disposable fields but is not disposable

internal sealed class PostgresTestStore : TestStore
{
    public static PostgresTestStore Instance { get; } = new();

    private static readonly PostgreSqlContainer s_container = new PostgreSqlBuilder()
        .WithImage("pgvector/pgvector:pg18")
        .Build();

    private NpgsqlDataSource? _dataSource;
    private string? _connectionString;
    private bool _useExternalInstance;

    public NpgsqlDataSource DataSource => this._dataSource ?? throw new InvalidOperationException("Not initialized");

    public string ConnectionString => this._connectionString ?? throw new InvalidOperationException("Not initialized");

    public PostgresVectorStore GetVectorStore(PostgresVectorStoreOptions options)
    {
        // The DataSource is shared with the static instance, we don't want any of the tests to dispose it.
        return new(this.DataSource, ownsDataSource: false, options);
    }

    private PostgresTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        // Determine connection string source
        if (PostgresTestEnvironment.IsConnectionStringDefined)
        {
            this._connectionString = PostgresTestEnvironment.ConnectionString!;
            this._useExternalInstance = true;
        }
        else
        {
            // Use testcontainer if no external connection string is provided
            await s_container.StartAsync();

            NpgsqlConnectionStringBuilder connectionStringBuilder = new()
            {
                Host = s_container.Hostname,
                Port = s_container.GetMappedPublicPort(5432),
                Username = PostgreSqlBuilder.DefaultUsername,
                Password = PostgreSqlBuilder.DefaultPassword,
                Database = PostgreSqlBuilder.DefaultDatabase
            };

            this._connectionString = connectionStringBuilder.ConnectionString;
            this._useExternalInstance = false;
        }

        NpgsqlDataSourceBuilder dataSourceBuilder = new(this._connectionString!);
        dataSourceBuilder.UseVector();
        this._dataSource = dataSourceBuilder.Build();

        // It's a shared static instance, we don't want any of the tests to dispose it.
        this.DefaultVectorStore = new PostgresVectorStore(this._dataSource, ownsDataSource: false);
    }

    protected override async Task StopAsync()
    {
        if (this._dataSource is not null)
        {
            await this._dataSource.DisposeAsync();
        }

        // Only stop the container if we started it
        if (!this._useExternalInstance)
        {
            await s_container.StopAsync();
        }
    }
}
