// Copyright (c) Microsoft. All rights reserved.

using System.Linq;
using System.Threading.Tasks;
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
}
