// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Npgsql;
using Testcontainers.PostgreSql;
using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Support;

internal sealed class PostgresTestStore : TestStore
{
    public static PostgresTestStore Instance { get; } = new();

    private static readonly PostgreSqlContainer s_container = new PostgreSqlBuilder()
        .WithImage("pgvector/pgvector:pg16")
        .Build();

    private NpgsqlDataSource? _dataSource;
    private PostgresVectorStore? _defaultVectorStore;

    public NpgsqlDataSource DataSource => this._dataSource ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public PostgresVectorStore GetVectorStore(PostgresVectorStoreOptions options)
        => new(this.DataSource, options);

    private PostgresTestStore()
    {
    }

    protected override async Task StartAsync()
    {
        await s_container.StartAsync();

        var dataSourceBuilder = new NpgsqlDataSourceBuilder
        {
            ConnectionStringBuilder =
            {
                Host = s_container.Hostname,
                Port = s_container.GetMappedPublicPort(5432),
                Username = PostgreSqlBuilder.DefaultUsername,
                Password = PostgreSqlBuilder.DefaultPassword,
                Database = PostgreSqlBuilder.DefaultDatabase
            }
        };

        dataSourceBuilder.UseVector();

        this._dataSource = dataSourceBuilder.Build();

        await using var connection = this._dataSource.CreateConnection();
        await connection.OpenAsync();
        using var command = new NpgsqlCommand("CREATE EXTENSION IF NOT EXISTS vector", connection);
        await command.ExecuteNonQueryAsync();
        await connection.ReloadTypesAsync();

        this._defaultVectorStore = new(this._dataSource);
    }

    protected override async Task StopAsync()
    {
        await this._dataSource!.DisposeAsync();
        await s_container.StopAsync();
    }
}
