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
        .WithImage("pgvector/pgvector:pg16")
        .Build();

    private NpgsqlDataSource? _dataSource;
    private string? _connectionString;

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

        NpgsqlDataSourceBuilder dataSourceBuilder = new(connectionStringBuilder.ConnectionString);
        dataSourceBuilder.UseVector();

        this._dataSource = dataSourceBuilder.Build();

        await using var connection = this._dataSource.CreateConnection();
        await connection.OpenAsync();
        using var command = new NpgsqlCommand("CREATE EXTENSION IF NOT EXISTS vector", connection);
        await command.ExecuteNonQueryAsync();
        await connection.ReloadTypesAsync();

        // It's a shared static instance, we don't want any of the tests to dispose it.
        this.DefaultVectorStore = new PostgresVectorStore(this._dataSource, ownsDataSource: false);
    }

    protected override async Task StopAsync()
    {
        if (this._dataSource is not null)
        {
            await this._dataSource.DisposeAsync();
        }

        await s_container.StopAsync();
    }
}
