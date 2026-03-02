// Copyright (c) Microsoft. All rights reserved.

using System.Linq.Expressions;
using Microsoft.Data.SqlClient;
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

    public override async Task WaitForDataAsync<TKey, TRecord>(
        VectorStoreCollection<TKey, TRecord> collection,
        int recordCount,
        Expression<Func<TRecord, bool>>? filter = null,
        Expression<Func<TRecord, object?>>? vectorProperty = null,
        int? vectorSize = null,
        object? dummyVector = null)
    {
        // First wait for the base data to be visible via vector search
        await base.WaitForDataAsync(collection, recordCount, filter, vectorProperty, vectorSize, dummyVector);

        // Then wait for full-text population to complete (if any full-text indexes exist)
        await this.WaitForFullTextPopulationAsync(collection.Name);
    }

    private async Task WaitForFullTextPopulationAsync(string tableName)
    {
        using var connection = new SqlConnection(this.ConnectionString);
        await connection.OpenAsync();

        // Query to check if full-text population is complete
        var checkSql = @"
            SELECT COUNT(*)
            FROM sys.fulltext_indexes fi
            JOIN sys.tables t ON fi.object_id = t.object_id
            WHERE t.name = @tableName
              AND fi.has_crawl_completed = 0";

        using var command = new SqlCommand(checkSql, connection);
        command.Parameters.AddWithValue("@tableName", tableName);

        for (int i = 0; i < 100; i++) // Wait up to 10 seconds
        {
            var result = await command.ExecuteScalarAsync();

            if (result is int count && count == 0)
            {
                // Either no full-text indexes exist or all are populated
                return;
            }

            await Task.Delay(TimeSpan.FromMilliseconds(100));
        }

        // Don't fail the test - some tests might not need full-text
    }
}
