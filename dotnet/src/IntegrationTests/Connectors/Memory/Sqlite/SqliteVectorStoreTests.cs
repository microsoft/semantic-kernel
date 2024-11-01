﻿// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

/// <summary>
/// Integration tests for <see cref="SqliteVectorStore"/> class.
/// </summary>
[Collection("SqliteVectorStoreCollection")]
public sealed class SqliteVectorStoreTests(SqliteVectorStoreFixture fixture)
{
    private const string? SkipReason = "SQLite vector search extension is required";

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAListOfExistingCollectionNamesAsync()
    {
        // Arrange
        var sut = new SqliteVectorStore(fixture.Connection!);

        var collection1 = fixture.GetCollection<SqliteHotel<string>>("ListCollectionNames1");
        var collection2 = fixture.GetCollection<SqliteHotel<string>>("ListCollectionNames2");

        await collection1.CreateCollectionIfNotExistsAsync();
        await collection2.CreateCollectionIfNotExistsAsync();

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("ListCollectionNames1", collectionNames);
        Assert.Contains("ListCollectionNames1", collectionNames);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanGetAListOfExistingCollectionNamesWhenRegisteredWithDIAsync()
    {
        // Arrange
        var serviceCollection = new ServiceCollection();

        serviceCollection.AddSqliteVectorStore(connectionString: "Data Source=:memory:");

        var provider = serviceCollection.BuildServiceProvider();

        var sut = provider.GetRequiredService<IVectorStore>();

        var collection1 = sut.GetCollection<string, SqliteHotel<string>>("ListCollectionNames1");
        var collection2 = sut.GetCollection<string, SqliteHotel<string>>("ListCollectionNames2");

        await collection1.CreateCollectionIfNotExistsAsync();
        await collection2.CreateCollectionIfNotExistsAsync();

        // Act
        var collectionNames = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("ListCollectionNames1", collectionNames);
        Assert.Contains("ListCollectionNames1", collectionNames);
    }
}
