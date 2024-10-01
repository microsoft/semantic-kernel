// Copyright (c) Microsoft. All rights reserved.

using System.Threading.Tasks;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Xunit;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Sqlite;

/// <summary>
/// Integration tests for <see cref="SqliteVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
[Collection("SqliteVectorStoreCollection")]
public sealed class SqliteVectorStoreRecordCollectionTests(SqliteVectorStoreFixture fixture)
{
    //private const string? SkipReason = "SQLite vector search extension is required";
    private const string? SkipReason = null;

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(bool createCollection)
    {
        // Arrange
        var sut = new SqliteVectorStoreRecordCollection<SqliteHotel<ulong>>(fixture.Connection, "CollectionExists");

        if (createCollection)
        {
            await sut.CreateCollectionAsync();
        }

        // Act
        var collectionExists = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(createCollection, collectionExists);
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanCreateCollectionAsync()
    {
        // Arrange
        var sut = new SqliteVectorStoreRecordCollection<SqliteHotel<ulong>>(fixture.Connection, "CreateCollection");

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        Assert.True(await sut.CollectionExistsAsync());
    }

    [Fact(Skip = SkipReason)]
    public async Task ItCanDeleteCollectionAsync()
    {
        // Arrange
        var sut = new SqliteVectorStoreRecordCollection<SqliteHotel<ulong>>(fixture.Connection, "DeleteCollection");

        await sut.CreateCollectionAsync();

        Assert.True(await sut.CollectionExistsAsync());

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        Assert.False(await sut.CollectionExistsAsync());
    }
}
