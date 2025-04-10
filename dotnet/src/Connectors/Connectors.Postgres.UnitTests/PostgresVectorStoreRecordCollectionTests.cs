// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Moq;
using Pgvector;
using Xunit;

namespace SemanticKernel.Connectors.Postgres.UnitTests;

public class PostgresVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";

    private readonly Mock<IPostgresVectorStoreDbClient> _postgresClientMock;
    private readonly CancellationToken _testCancellationToken = new(false);

    public PostgresVectorStoreRecordCollectionTests()
    {
        this._postgresClientMock = new Mock<IPostgresVectorStoreDbClient>(MockBehavior.Strict);
        this._postgresClientMock.Setup(l => l.DatabaseName).Returns("TestDatabase");
    }

    [Fact]
    public async Task CreatesCollectionForGenericModelAsync()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties = [
                new VectorStoreRecordKeyProperty("HotelId", typeof(int)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsIndexed = true, IsFullTextIndexed = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { IsIndexed = true, StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)) { IsIndexed = true },
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?), 100) { DistanceFunction = DistanceFunction.ManhattanDistance }
            ]
        };
        var options = new PostgresVectorStoreRecordCollectionOptions<Dictionary<string, object?>>()
        {
            VectorStoreRecordDefinition = recordDefinition
        };
        var sut = new PostgresVectorStoreRecordCollection<object, Dictionary<string, object?>>(this._postgresClientMock.Object, TestCollectionName, options);
        this._postgresClientMock.Setup(x => x.DoesTableExistsAsync(TestCollectionName, this._testCancellationToken)).ReturnsAsync(false);

        // Act
        var exists = await sut.CollectionExistsAsync();

        // Assert.
        Assert.False(exists);
    }

    [Fact]
    public void ThrowsForUnsupportedType()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties = [
                new VectorStoreRecordKeyProperty("HotelId", typeof(ulong)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsIndexed = true, IsFullTextIndexed = true },
            ]
        };
        var options = new PostgresVectorStoreRecordCollectionOptions<Dictionary<string, object?>>()
        {
            VectorStoreRecordDefinition = recordDefinition
        };

        // Act & Assert
        Assert.Throws<NotSupportedException>(() => new PostgresVectorStoreRecordCollection<object, Dictionary<string, object?>>(this._postgresClientMock.Object, TestCollectionName, options));
    }

    [Fact]
    public async Task UpsertRecordAsyncProducesExpectedClientCallAsync()
    {
        // Arrange
        Dictionary<string, object?>? capturedArguments = null;

        var sut = new PostgresVectorStoreRecordCollection<int, PostgresHotel<int>>(this._postgresClientMock.Object, TestCollectionName);
        var record = new PostgresHotel<int>
        {
            HotelId = 1,
            HotelName = "Hotel 1",
            HotelCode = 1,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = ["tag1", "tag2"],
            Description = "A hotel",
            DescriptionEmbedding = new ReadOnlyMemory<float>([1.0f, 2.0f, 3.0f, 4.0f])
        };

        this._postgresClientMock.Setup(x => x.UpsertAsync(
            TestCollectionName,
            It.IsAny<Dictionary<string, object?>>(),
            "HotelId",
            this._testCancellationToken))
            .Callback<string, Dictionary<string, object?>, string, CancellationToken>((collectionName, args, key, ct) => capturedArguments = args)
            .Returns(Task.CompletedTask);

        // Act
        await sut.UpsertAsync(record, cancellationToken: this._testCancellationToken);

        // Assert
        Assert.NotNull(capturedArguments);
        Assert.Equal(1, (int)(capturedArguments["HotelId"] ?? 0));
        Assert.Equal("Hotel 1", (string)(capturedArguments["HotelName"] ?? ""));
        Assert.Equal(1, (int)(capturedArguments["HotelCode"] ?? 0));
        Assert.Equal(4.5f, (float)(capturedArguments["HotelRating"] ?? 0.0f));
        Assert.True((bool)(capturedArguments["parking_is_included"] ?? false));
        Assert.True(capturedArguments["Tags"] is List<string>);
        var tags = capturedArguments["Tags"] as List<string>;
        Assert.Equal(2, tags!.Count);
        Assert.Equal("tag1", tags[0]);
        Assert.Equal("tag2", tags[1]);
        Assert.Equal("A hotel", (string)(capturedArguments["Description"] ?? ""));
        Assert.NotNull(capturedArguments["DescriptionEmbedding"]);
        Assert.IsType<Vector>(capturedArguments["DescriptionEmbedding"]);
        var embedding = ((Vector)capturedArguments["DescriptionEmbedding"]!).ToArray();
        Assert.Equal(1.0f, embedding[0]);
        Assert.Equal(2.0f, embedding[1]);
        Assert.Equal(3.0f, embedding[2]);
        Assert.Equal(4.0f, embedding[3]);
    }

    [Fact]
    public async Task CollectionExistsReturnsValidResultAsync()
    {
        // Arrange
        const string TableName = "CollectionExists";

        this._postgresClientMock.Setup(x => x.DoesTableExistsAsync(TableName, this._testCancellationToken)).ReturnsAsync(true);

        var sut = new PostgresVectorStoreRecordCollection<int, TestRecord<int>>(this._postgresClientMock.Object, TableName);

        // Act
        var result = await sut.CollectionExistsAsync();

        Assert.True(result);
    }

    [Fact]
    public async Task DeleteCollectionCallsClientDeleteAsync()
    {
        // Arrange
        const string TableName = "DeleteCollection";

        this._postgresClientMock.Setup(x => x.DeleteTableAsync(TableName, this._testCancellationToken)).Returns(Task.CompletedTask);

        var sut = new PostgresVectorStoreRecordCollection<int, TestRecord<int>>(this._postgresClientMock.Object, TableName);

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        this._postgresClientMock.Verify(x => x.DeleteTableAsync(TableName, this._testCancellationToken), Times.Once);
    }

    #region private

    private static void AssertRecord<TKey>(TestRecord<TKey> expectedRecord, TestRecord<TKey>? actualRecord, bool includeVectors)
    {
        Assert.NotNull(actualRecord);

        Assert.Equal(expectedRecord.Key, actualRecord.Key);
        Assert.Equal(expectedRecord.Data, actualRecord.Data);

        if (includeVectors)
        {
            Assert.NotNull(actualRecord.Vector);
            Assert.Equal(expectedRecord.Vector!.Value.ToArray(), actualRecord.Vector.Value.Span.ToArray());
        }
        else
        {
            Assert.Null(actualRecord.Vector);
        }
    }

#pragma warning disable CA1812
    private sealed class TestRecord<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; }

        [VectorStoreRecordData]
        public string? Data { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.CosineDistance)]
        public ReadOnlyMemory<float>? Vector { get; set; }
    }

    private sealed class TestRecordWithoutVectorProperty<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; }

        [VectorStoreRecordData]
        public string? Data { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
