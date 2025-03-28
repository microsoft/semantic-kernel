// Copyright (c) Microsoft. All rights reserved.

// TODO: Reimplement these as integration tests, #10464

#if DISABLED

using System;
using System.Data.Common;
using System.Linq;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Data.Sqlite;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Sqlite;
using Moq;
using Xunit;

namespace SemanticKernel.Connectors.Sqlite.UnitTests;

/// <summary>
/// Unit tests for <see cref="SqliteVectorStore"/> class.
/// </summary>
public sealed class SqliteVectorStoreTests
{
    [Fact]
    public void GetCollectionWithNotSupportedKeyThrowsException()
    {
        // Arrange
        var sut = new SqliteVectorStore(Mock.Of<SqliteConnection>());

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => sut.GetCollection<int, SqliteHotel<int>>("collection"));
    }

    [Fact]
    public void GetCollectionWithSupportedKeyReturnsCollection()
    {
        // Arrange
        var sut = new SqliteVectorStore(Mock.Of<SqliteConnection>());

        // Act
        var collectionWithNumericKey = sut.GetCollection<ulong, SqliteHotel<ulong>>("collection1");
        var collectionWithStringKey = sut.GetCollection<string, SqliteHotel<string>>("collection2");

        // Assert
        Assert.NotNull(collectionWithNumericKey);
        Assert.NotNull(collectionWithStringKey);
    }

#pragma warning disable CS0618 // ISqliteVectorStoreRecordCollectionFactory is obsolete
    [Fact]
    public void GetCollectionWithFactoryReturnsCustomCollection()
    {
        // Arrange
        var mockFactory = new Mock<ISqliteVectorStoreRecordCollectionFactory>();
        var mockRecordCollection = new Mock<IVectorStoreRecordCollection<string, SqliteHotel<string>>>();
        var mockConnection = Mock.Of<SqliteConnection>();

        mockFactory
            .Setup(l => l.CreateVectorStoreRecordCollection<string, SqliteHotel<string>>(
                mockConnection,
                "collection",
                It.IsAny<VectorStoreRecordDefinition>()))
            .Returns(mockRecordCollection.Object);

        var sut = new SqliteVectorStore(
            mockConnection,
            new SqliteVectorStoreOptions { VectorStoreCollectionFactory = mockFactory.Object });

        // Act
        var collection = sut.GetCollection<string, SqliteHotel<string>>("collection");

        // Assert
        Assert.Same(mockRecordCollection.Object, collection);
        mockFactory.Verify(l => l.CreateVectorStoreRecordCollection<string, SqliteHotel<string>>(
            mockConnection,
            "collection",
            It.IsAny<VectorStoreRecordDefinition>()), Times.Once());
    }
#pragma warning restore CS0618

    [Fact]
    public async Task ListCollectionNamesReturnsCollectionNamesAsync()
    {
        // Arrange
        var mockReader = new Mock<DbDataReader>();
        mockReader
            .SetupSequence(l => l.ReadAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(true)
            .ReturnsAsync(true)
            .ReturnsAsync(false);

        mockReader
            .SetupSequence(l => l.GetString(It.IsAny<int>()))
            .Returns("collection1")
            .Returns("collection2");

        using var fakeCommand = new FakeDbCommand(mockReader.Object);
        using var fakeConnection = new FakeDBConnection(fakeCommand);

        var sut = new SqliteVectorStore(fakeConnection);

        // Act
        var collections = await sut.ListCollectionNamesAsync().ToListAsync();

        // Assert
        Assert.Contains("collection1", collections);
        Assert.Contains("collection2", collections);
    }
}

#endif
