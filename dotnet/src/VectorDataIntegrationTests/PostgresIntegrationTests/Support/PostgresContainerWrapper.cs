// Copyright (c) Microsoft. All rights reserved.

using Microsoft.SemanticKernel.Connectors.Postgres;
using Npgsql;
using Testcontainers.PostgreSql;

namespace PostgresIntegrationTests.Support;

#pragma warning disable SKEXP0020 // PostgresVectorStore is experimental

public class PostgresContainerWrapper : IAsyncDisposable
{
    private static readonly PostgreSqlContainer s_container = new PostgreSqlBuilder()
        .WithImage("pgvector/pgvector:pg16")
        .Build();
    private static NpgsqlDataSource? s_dataSource;
    private static PostgresVectorStore? s_defaultVectorStore;

    private static readonly SemaphoreSlim s_lock = new(1, 1);
    private static int s_referenceCount;

    public NpgsqlDataSource DataSource => s_dataSource ?? throw new InvalidOperationException("Not initialized");
    public PostgresVectorStore DefaultVectorStore => s_defaultVectorStore ?? throw new InvalidOperationException("Not initialized");

    private PostgresContainerWrapper()
    {
    }

    public static async Task<PostgresContainerWrapper> GetAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (s_referenceCount++ == 0)
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

                s_dataSource = dataSourceBuilder.Build();

                await using var connection = s_dataSource.CreateConnection();
                await connection.OpenAsync();
                await using var command = new NpgsqlCommand("CREATE EXTENSION IF NOT EXISTS vector", connection);
                await command.ExecuteNonQueryAsync();
                await connection.ReloadTypesAsync();

                s_defaultVectorStore = new(s_dataSource);
            }
        }
        finally
        {
            s_lock.Release();
        }

        return new();
    }

    public async ValueTask DisposeAsync()
    {
        await s_lock.WaitAsync();
        try
        {
            if (--s_referenceCount == 0)
            {
                await s_dataSource!.DisposeAsync();
                await s_container.StopAsync();
            }
        }
        finally
        {
            s_lock.Release();
        }

        GC.SuppressFinalize(this);
    }
}
