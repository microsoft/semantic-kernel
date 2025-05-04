﻿// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteServiceCollectionExtensions"/> class.
/// </summary>
public sealed class SqliteServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Act
        this._serviceCollection.AddSqliteVectorStore("Data Source=:memory:");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<VectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<SqliteVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithStringKeyRegistersClass()
    {
        // Act
        this._serviceCollection.AddSqliteVectorStoreRecordCollection<string, TestRecord>("testcollection", "Data Source=:memory:");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        // Assert
        var collection = serviceProvider.GetRequiredService<VectorStoreCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteCollection<string, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteCollection<string, TestRecord>>(vectorizedSearch);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionWithNumericKeyRegistersClass()
    {
        // Act
        this._serviceCollection.AddSqliteVectorStoreRecordCollection<ulong, TestRecord>("testcollection", "Data Source=:memory:");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        // Assert
        var collection = serviceProvider.GetRequiredService<VectorStoreCollection<ulong, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<SqliteCollection<ulong, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<SqliteCollection<ulong, TestRecord>>(vectorizedSearch);
    }

    #region private

#pragma warning disable CA1812 // Avoid uninstantiated internal classes
    private sealed class TestRecord
#pragma warning restore CA1812 // Avoid uninstantiated internal classes
    {
        [VectorStoreKey]
        public string Id { get; set; } = string.Empty;
    }

    #endregion
}
