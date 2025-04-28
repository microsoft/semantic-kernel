// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Npgsql;
using Xunit;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

/// <summary>
/// Unit tests for <see cref="PostgresServiceCollectionExtensions"/> class.
/// </summary>
public sealed class PostgresServiceCollectionExtensionsTests
{
    private readonly IServiceCollection _serviceCollection = new ServiceCollection();

    [Fact]
    public void AddVectorStoreRegistersClass()
    {
        // Arrange
        using var dataSource = NpgsqlDataSource.Create("Host=fake;");
        this._serviceCollection.AddSingleton<NpgsqlDataSource>(dataSource);

        // Act
        this._serviceCollection.AddPostgresVectorStore();

        var serviceProvider = this._serviceCollection.BuildServiceProvider();
        var vectorStore = serviceProvider.GetRequiredService<IVectorStore>();

        // Assert
        Assert.NotNull(vectorStore);
        Assert.IsType<PostgresVectorStore>(vectorStore);
    }

    [Fact]
    public void AddVectorStoreRecordCollectionRegistersClass()
    {
        // Arrange
        using var dataSource = NpgsqlDataSource.Create("Host=fake;");
        this._serviceCollection.AddSingleton<NpgsqlDataSource>(dataSource);

        // Act
        this._serviceCollection.AddPostgresVectorStoreRecordCollection<string, TestRecord>("testcollection");

        var serviceProvider = this._serviceCollection.BuildServiceProvider();

        // Assert
        var collection = serviceProvider.GetRequiredService<IVectorStoreRecordCollection<string, TestRecord>>();
        Assert.NotNull(collection);
        Assert.IsType<PostgresVectorStoreRecordCollection<string, TestRecord>>(collection);

        var vectorizedSearch = serviceProvider.GetRequiredService<IVectorSearch<TestRecord>>();
        Assert.NotNull(vectorizedSearch);
        Assert.IsType<PostgresVectorStoreRecordCollection<string, TestRecord>>(vectorizedSearch);
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
