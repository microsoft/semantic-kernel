// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Postgres;
using Moq;
using Pgvector;
using Xunit;

namespace SemanticKernel.Connectors.UnitTests.Postgres;

public class PostgresVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";

    private readonly Mock<IPostgresVectorStoreDbClient> _postgresClientMock;
    private readonly CancellationToken _testCancellationToken = new(false);

    public PostgresVectorStoreRecordCollectionTests()
    {
        this._postgresClientMock = new Mock<IPostgresVectorStoreDbClient>(MockBehavior.Strict);
    }

    [Fact]
    public async Task CreatesCollectionForGenericModelAsync()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties = [
                new VectorStoreRecordKeyProperty("HotelId", typeof(int)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { IsFilterable = true, StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 100, DistanceFunction = DistanceFunction.ManhattanDistance }
            ]
        };
        var options = new PostgresVectorStoreRecordCollectionOptions<VectorStoreGenericDataModel<int>>()
        {
            VectorStoreRecordDefinition = recordDefinition
        };
        var sut = new PostgresVectorStoreRecordCollection<ulong, VectorStoreGenericDataModel<int>>(this._postgresClientMock.Object, TestCollectionName, options);
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
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
            ]
        };
        var options = new PostgresVectorStoreRecordCollectionOptions<VectorStoreGenericDataModel<ulong>>()
        {
            VectorStoreRecordDefinition = recordDefinition
        };

        // Act & Assert
        Assert.Throws<ArgumentException>(() => new PostgresVectorStoreRecordCollection<ulong, VectorStoreGenericDataModel<ulong>>(this._postgresClientMock.Object, TestCollectionName, options));
    }

    [Fact]
    public async Task UpsertRecordAsyncProducesExpectedSqlAsync()
    {
        // Arrange
        Dictionary<string, object?>? capturedArguments = null;

        var sut = new PostgresVectorStoreRecordCollection<int, PostgresHotel>(this._postgresClientMock.Object, TestCollectionName);
        var record = new PostgresHotel
        {
            HotelId = 1,
            HotelName = "Hotel 1",
            HotelCode = 1,
            HotelRating = 4.5f,
            ParkingIncluded = true,
            Tags = ["tag1", "tag2"],
            Description = "A hotel",
            DescriptionEmbedding = new ReadOnlyMemory<float>(new float[] { 1.0f, 2.0f, 3.0f, 4.0f })
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
    public async Task CreateCollectionAsyncLogsWarningWhenDimensionsTooLargeAsync()
    {
        // Arrange
        var recordDefinition = new VectorStoreRecordDefinition
        {
            Properties = [
                new VectorStoreRecordKeyProperty("HotelId", typeof(int)),
                new VectorStoreRecordDataProperty("HotelName", typeof(string)) { IsFilterable = true, IsFullTextSearchable = true },
                new VectorStoreRecordDataProperty("HotelCode", typeof(int)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("ParkingIncluded", typeof(bool)) { IsFilterable = true, StoragePropertyName = "parking_is_included" },
                new VectorStoreRecordDataProperty("HotelRating", typeof(float)) { IsFilterable = true },
                new VectorStoreRecordDataProperty("Tags", typeof(List<string>)),
                new VectorStoreRecordDataProperty("Description", typeof(string)),
                new VectorStoreRecordVectorProperty("DescriptionEmbedding", typeof(ReadOnlyMemory<float>?)) { Dimensions = 2001, IndexKind = IndexKind.Hnsw, DistanceFunction = DistanceFunction.ManhattanDistance }
            ]
        };
        var mockLogger = new Mock<ILogger<PostgresVectorStoreRecordCollection<int, PostgresHotel>>>();
        mockLogger.Setup(x => x.Log(
            LogLevel.Warning,
            It.IsAny<EventId>(),
            It.IsAny<It.IsAnyType>(),
            It.IsAny<Exception>(),
            It.IsAny<Func<It.IsAnyType, Exception?, string>>()));
        var sut = new PostgresVectorStoreRecordCollection<int, PostgresHotel>(
            this._postgresClientMock.Object,
            TestCollectionName,
            logger: mockLogger.Object,
            options: new PostgresVectorStoreRecordCollectionOptions<PostgresHotel> { VectorStoreRecordDefinition = recordDefinition }
        );

        this._postgresClientMock.Setup(x => x.CreateTableAsync(TestCollectionName, It.IsAny<VectorStoreRecordDefinition>(), It.IsAny<bool>(), It.IsAny<CancellationToken>())).Returns(Task.CompletedTask);

        // Act
        await sut.CreateCollectionAsync(cancellationToken: this._testCancellationToken);

        // Assert
        mockLogger.Verify(
            x => x.Log(
                LogLevel.Warning,
                It.IsAny<EventId>(),
                It.Is<It.IsAnyType>((v, t) => v.ToString()!.Contains("2001")),
                It.IsAny<Exception>(),
                It.IsAny<Func<It.IsAnyType, Exception?, string>>()),
            Times.Once);
    }
}
