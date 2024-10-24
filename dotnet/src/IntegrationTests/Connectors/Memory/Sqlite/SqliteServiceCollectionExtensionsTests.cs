﻿// Copyright (c) Microsoft. All rights reserved.

using System.Data;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

/// <summary>
/// Integration tests for <see cref="SqliteServiceCollectionExtensions"/> class.
/// </summary>
public sealed class SqliteServiceCollectionExtensionsTests
{
    private const string? SkipReason = "SQLite vector search extension is required";

    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Fact(Skip = SkipReason)]
    public void AddVectorStoreWithSqliteConnectionRegistersClass()
    {
        // Act
        this._serviceCollection.AddSqliteVectorStore("Data Source=:memory:");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<SqliteVectorStore>(vectorStore);
    }

    [Fact(Skip = SkipReason)]
    public void AddVectorStoreRecordCollectionWithStringKeyAndSqliteConnectionRegistersClass()
    {
        // Act
        this._serviceCollection.AddSqliteVectorStoreRecordCollection<string, TestRecord>("testcollection", "Data Source=:memory:");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        // Assert
        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);
    }

    [Fact(Skip = SkipReason)]
    public void AddVectorStoreRecordCollectionWithNumericKeyAndSqliteConnectionRegistersClass()
    {
        // Act
        this._serviceCollection.AddSqliteVectorStoreRecordCollection<ulong, TestRecord>("testcollection", "Data Source=:memory:");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        // Assert
        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<ulong, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorizedSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteVectorStoreRecordCollection<TestRecord>>(vectorizedSearch);
    }

    [Fact(Skip = SkipReason)]
    public void ItClosesConnectionWhenDIServiceIsDisposed()
    {
        // Act
        using var connection = new SqliteConnection("Data Source=:memory:");

        this._serviceCollection.AddTransient<SqliteConnection>(_ => connection);

        this._serviceCollection.AddSqliteVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        using (var scope = serviceProvider.CreateScope())
        {
            scope.ServiceProvider.GetRequiredService<IVectorStore>();

            Assert.Equal(ConnectionState.Open, connection.State);
        }

        // Assert
        Assert.Equal(ConnectionState.Closed, connection.State);
    }

    #region private

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreRecordKey]
        public string Id { get; set; } = string.Empty;
    }

    #endregion
}
