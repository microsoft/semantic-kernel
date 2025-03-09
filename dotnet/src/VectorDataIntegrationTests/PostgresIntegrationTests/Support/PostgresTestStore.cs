// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Npgsql;
using Testcontainers.PostgreSql;
using VectorDataSpecificationTests.Support;

namespace PostgresIntegrationTests.Support;

#pragma warning disable SKEXP0020

public sealed class PostgresTestStore : TestStore
{
    public static PostgresTestStore Instance { get; } = new();

    private static readonly PostgreSqlContainer s_container = new PostgreSqlBuilder()
        .WithImage("pgvector/pgvector:pg16")
        .Build();

    private readonly string? _externalConnectionString;
    private NpgsqlDataSource? _dataSource;
    private PostgresVectorStore? _defaultVectorStore;

    public NpgsqlDataSource DataSource => this._dataSource ?? throw new InvalidOperationException("Not initialized");

    public override IVectorStore DefaultVectorStore => this._defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    public PostgresVectorStore GetVectorStore(PostgresVectorStoreOptions options)
        => new(this.DataSource, options);

    private PostgresTestStore()
    {
        var configuration = new ConfigurationBuilder()
            .AddJsonFile(path: "testsettings.json", optional: true)
            .AddJsonFile(path: "testsettings.development.json", optional: true)
            .AddEnvironmentVariables()
            .Build();

        var pgSection = configuration.GetSection("PostgreSQL");
        this._externalConnectionString = pgSection?["ConnectionString"];
    }

    protected override async Task StartAsync()
    {
        NpgsqlDataSourceBuilder dataSourceBuilder;

        if (this._externalConnectionString is null)
        {
            await s_container.StartAsync();

            dataSourceBuilder = new NpgsqlDataSourceBuilder
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
        }
        else
        {
            dataSourceBuilder = new NpgsqlDataSourceBuilder(this._externalConnectionString);
        }

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
