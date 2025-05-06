// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json;
using System.Text.Json.Nodes;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Azure.Cosmos;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.AzureCosmosDBNoSQL;
using Moq;
using Xunit;
using DistanceFunction = Microsoft.Extensions.VectorData.DistanceFunction;
using IndexKind = Microsoft.Extensions.VectorData.IndexKind;

namespace SemanticKernel.Connectors.AzureCosmosDBNoSQL.UnitTests;

/// <summary>
/// Unit tests for <see cref="AzureCosmosDBNoSQLVectorStoreRecordCollection{TKey, TRecord}"/> class.
/// </summary>
public sealed class AzureCosmosDBNoSQLVectorStoreRecordCollectionTests
{
    private readonly Mock<Database> _mockDatabase = new();
    private readonly Mock<Container> _mockContainer = new();

    public AzureCosmosDBNoSQLVectorStoreRecordCollectionTests()
    {
        this._mockDatabase.Setup(l => l.GetContainer(It.IsAny<string>())).Returns(this._mockContainer.Object);

        var mockClient = new Mock<CosmosClient>();

        mockClient.Setup(l => l.ClientOptions).Returns(new CosmosClientOptions() { UseSystemTextJsonSerializerWithOptions = JsonSerializerOptions.Default });

        this._mockDatabase
            .Setup(l => l.Client)
            .Returns(mockClient.Object);
    }

    [Fact]
    public void ConstructorForModelWithoutKeyThrowsException()
    {
        // Act & Assert
        var exception = Assert.Throws<NotSupportedException>(() => new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, object>(this._mockDatabase.Object, "collection"));
        Assert.Contains("No key property found", exception.Message);
    }

    [Fact]
    public void ConstructorWithoutSystemTextJsonSerializerOptionsThrowsArgumentException()
    {
        // Arrange
        var mockDatabase = new Mock<Database>();
        var mockClient = new Mock<CosmosClient>();

        mockDatabase.Setup(l => l.Client).Returns(mockClient.Object);

        // Act & Assert
        var exception = Assert.Throws<ArgumentException>(() => new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(mockDatabase.Object, "collection"));
        Assert.Contains(nameof(CosmosClientOptions.UseSystemTextJsonSerializerWithOptions), exception.Message);
    }

    [Fact]
    public void ConstructorWithDeclarativeModelInitializesCollection()
    {
        // Act & Assert
        var collection = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        Assert.NotNull(collection);
    }

    [Fact]
    public void ConstructorWithImperativeModelInitializesCollection()
    {
        // Arrange
        var definition = new VectorStoreRecordDefinition
        {
            Properties = [new VectorStoreRecordKeyProperty("Id", typeof(string))]
        };

        // Act
        var collection = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, TestModel>(
            this._mockDatabase.Object,
            "collection",
            new() { VectorStoreRecordDefinition = definition });

        // Assert
        Assert.NotNull(collection);
    }

    [Theory]
    [MemberData(nameof(CollectionExistsData))]
    public async Task CollectionExistsReturnsValidResultAsync(List<string> collections, string collectionName, bool expectedResult)
    {
        // Arrange
        var mockFeedResponse = new Mock<FeedResponse<string>>();
        mockFeedResponse
            .Setup(l => l.Resource)
            .Returns(collections);

        var mockFeedIterator = new Mock<FeedIterator<string>>();
        mockFeedIterator
            .SetupSequence(l => l.HasMoreResults)
            .Returns(true)
            .Returns(false);

        mockFeedIterator
            .Setup(l => l.ReadNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(mockFeedResponse.Object);

        this._mockDatabase
            .Setup(l => l.GetContainerQueryIterator<string>(
                It.IsAny<QueryDefinition>(),
                It.IsAny<string>(),
                It.IsAny<QueryRequestOptions>()))
            .Returns(mockFeedIterator.Object);

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            collectionName);

        // Act
        var actualResult = await sut.CollectionExistsAsync();

        // Assert
        Assert.Equal(expectedResult, actualResult);
    }

    [Theory]
    [InlineData(IndexingMode.Consistent)]
    [InlineData(IndexingMode.Lazy)]
    [InlineData(IndexingMode.None)]
    public async Task CreateCollectionUsesValidContainerPropertiesAsync(IndexingMode indexingMode)
    {
        // Arrange
        const string CollectionName = "collection";

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, TestIndexingModel>(
            this._mockDatabase.Object,
            CollectionName,
            new() { IndexingMode = indexingMode, Automatic = indexingMode != IndexingMode.None });

        var expectedVectorEmbeddingPolicy = new VectorEmbeddingPolicy(
        [
            new Embedding
            {
                DataType = VectorDataType.Float32,
                Dimensions = 2,
                DistanceFunction = Microsoft.Azure.Cosmos.DistanceFunction.Cosine,
                Path = "/DescriptionEmbedding2"
            },
            new Embedding
            {
                DataType = VectorDataType.Uint8,
                Dimensions = 3,
                DistanceFunction = Microsoft.Azure.Cosmos.DistanceFunction.DotProduct,
                Path = "/DescriptionEmbedding3"
            },
            new Embedding
            {
                DataType = VectorDataType.Int8,
                Dimensions = 4,
                DistanceFunction = Microsoft.Azure.Cosmos.DistanceFunction.Euclidean,
                Path = "/DescriptionEmbedding4"
            },
        ]);

        var expectedIndexingPolicy = new IndexingPolicy
        {
            VectorIndexes =
            [
                new VectorIndexPath { Type = VectorIndexType.Flat, Path = "/DescriptionEmbedding2" },
                new VectorIndexPath { Type = VectorIndexType.QuantizedFlat, Path = "/DescriptionEmbedding3" },
                new VectorIndexPath { Type = VectorIndexType.DiskANN, Path = "/DescriptionEmbedding4" },
            ],
            IndexingMode = indexingMode,
            Automatic = indexingMode != IndexingMode.None
        };

        if (indexingMode != IndexingMode.None)
        {
            expectedIndexingPolicy.IncludedPaths.Add(new IncludedPath { Path = "/IndexableData1/?" });
            expectedIndexingPolicy.IncludedPaths.Add(new IncludedPath { Path = "/IndexableData2/?" });
            expectedIndexingPolicy.IncludedPaths.Add(new IncludedPath { Path = "/" });

            expectedIndexingPolicy.ExcludedPaths.Add(new ExcludedPath { Path = "/DescriptionEmbedding2/*" });
            expectedIndexingPolicy.ExcludedPaths.Add(new ExcludedPath { Path = "/DescriptionEmbedding3/*" });
            expectedIndexingPolicy.ExcludedPaths.Add(new ExcludedPath { Path = "/DescriptionEmbedding4/*" });
        }

        var expectedContainerProperties = new ContainerProperties(CollectionName, "/id")
        {
            VectorEmbeddingPolicy = expectedVectorEmbeddingPolicy,
            IndexingPolicy = expectedIndexingPolicy
        };

        // Act
        await sut.CreateCollectionAsync();

        // Assert
        this._mockDatabase.Verify(l => l.CreateContainerAsync(
            It.Is<ContainerProperties>(properties => this.VerifyContainerProperties(expectedContainerProperties, properties)),
            It.IsAny<int?>(),
            It.IsAny<RequestOptions>(),
            It.IsAny<CancellationToken>()),
            Times.Once());
    }

    [Theory]
    [MemberData(nameof(CreateCollectionIfNotExistsData))]
    public async Task CreateCollectionIfNotExistsInvokesValidMethodsAsync(List<string> collections, int actualCollectionCreations)
    {
        // Arrange
        const string CollectionName = "collection";

        var mockFeedResponse = new Mock<FeedResponse<string>>();
        mockFeedResponse
            .Setup(l => l.Resource)
            .Returns(collections);

        var mockFeedIterator = new Mock<FeedIterator<string>>();
        mockFeedIterator
            .SetupSequence(l => l.HasMoreResults)
            .Returns(true)
            .Returns(false);

        mockFeedIterator
            .Setup(l => l.ReadNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(mockFeedResponse.Object);

        this._mockDatabase
            .Setup(l => l.GetContainerQueryIterator<string>(
                It.IsAny<QueryDefinition>(),
                It.IsAny<string>(),
                It.IsAny<QueryRequestOptions>()))
            .Returns(mockFeedIterator.Object);

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            CollectionName);

        // Act
        await sut.CreateCollectionIfNotExistsAsync();

        // Assert
        this._mockDatabase.Verify(l => l.CreateContainerAsync(
            It.IsAny<ContainerProperties>(),
            It.IsAny<int?>(),
            It.IsAny<RequestOptions>(),
            It.IsAny<CancellationToken>()),
            Times.Exactly(actualCollectionCreations));
    }

    [Theory]
    [InlineData("recordKey", false)]
    [InlineData("partitionKey", true)]
    public async Task DeleteInvokesValidMethodsAsync(
        string expectedPartitionKey,
        bool useCompositeKeyCollection)
    {
        // Arrange
        const string RecordKey = "recordKey";
        const string PartitionKey = "partitionKey";

        // Act
        if (useCompositeKeyCollection)
        {
            var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, AzureCosmosDBNoSQLHotel>(
                this._mockDatabase.Object,
                "collection");

            await ((IVectorStoreRecordCollection<AzureCosmosDBNoSQLCompositeKey, AzureCosmosDBNoSQLHotel>)sut).DeleteAsync(
                new AzureCosmosDBNoSQLCompositeKey(RecordKey, PartitionKey));
        }
        else
        {
            var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
                this._mockDatabase.Object,
                "collection");

            await ((IVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>)sut).DeleteAsync(
                RecordKey);
        }

        // Assert
        this._mockContainer.Verify(l => l.DeleteItemAsync<JsonObject>(
            RecordKey,
            new PartitionKey(expectedPartitionKey),
            It.IsAny<ItemRequestOptions>(),
            It.IsAny<CancellationToken>()),
            Times.Once());
    }

    [Fact]
    public async Task DeleteBatchInvokesValidMethodsAsync()
    {
        // Arrange
        List<string> recordKeys = ["key1", "key2"];

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act
        await sut.DeleteAsync(recordKeys);

        // Assert
        foreach (var key in recordKeys)
        {
            this._mockContainer.Verify(l => l.DeleteItemAsync<JsonObject>(
                key,
                new PartitionKey(key),
                It.IsAny<ItemRequestOptions>(),
                It.IsAny<CancellationToken>()),
                Times.Once());
        }
    }

    [Fact]
    public async Task DeleteCollectionInvokesValidMethodsAsync()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        this._mockContainer.Verify(l => l.DeleteContainerAsync(
            It.IsAny<ContainerRequestOptions>(),
            It.IsAny<CancellationToken>()),
            Times.Once());
    }

    [Fact]
    public async Task GetReturnsValidRecordAsync()
    {
        // Arrange
        const string RecordKey = "key";

        var jsonObject = new JsonObject { ["id"] = RecordKey, ["HotelName"] = "Test Name" };

        var mockFeedResponse = new Mock<FeedResponse<JsonObject>>();
        mockFeedResponse
            .Setup(l => l.Resource)
            .Returns([jsonObject]);

        var mockFeedIterator = new Mock<FeedIterator<JsonObject>>();
        mockFeedIterator
            .SetupSequence(l => l.HasMoreResults)
            .Returns(true)
            .Returns(false);

        mockFeedIterator
            .Setup(l => l.ReadNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(mockFeedResponse.Object);

        this._mockContainer
            .Setup(l => l.GetItemQueryIterator<JsonObject>(
                It.IsAny<QueryDefinition>(),
                It.IsAny<string>(),
                It.IsAny<QueryRequestOptions>()))
            .Returns(mockFeedIterator.Object);

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act
        var result = await sut.GetAsync(RecordKey);

        // Assert
        Assert.NotNull(result);
        Assert.Equal(RecordKey, result.HotelId);
        Assert.Equal("Test Name", result.HotelName);
    }

    [Fact]
    public async Task GetBatchReturnsValidRecordAsync()
    {
        // Arrange
        var jsonObject1 = new JsonObject { ["id"] = "key1", ["HotelName"] = "Test Name 1" };
        var jsonObject2 = new JsonObject { ["id"] = "key2", ["HotelName"] = "Test Name 2" };
        var jsonObject3 = new JsonObject { ["id"] = "key3", ["HotelName"] = "Test Name 3" };

        var mockFeedResponse = new Mock<FeedResponse<JsonObject>>();
        mockFeedResponse
            .Setup(l => l.Resource)
            .Returns([jsonObject1, jsonObject2, jsonObject3]);

        var mockFeedIterator = new Mock<FeedIterator<JsonObject>>();
        mockFeedIterator
            .SetupSequence(l => l.HasMoreResults)
            .Returns(true)
            .Returns(false);

        mockFeedIterator
            .Setup(l => l.ReadNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(mockFeedResponse.Object);

        this._mockContainer
            .Setup(l => l.GetItemQueryIterator<JsonObject>(
                It.IsAny<QueryDefinition>(),
                It.IsAny<string>(),
                It.IsAny<QueryRequestOptions>()))
            .Returns(mockFeedIterator.Object);

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act
        var results = await sut.GetAsync(["key1", "key2", "key3"]).ToListAsync();

        // Assert
        Assert.NotNull(results[0]);
        Assert.Equal("key1", results[0].HotelId);
        Assert.Equal("Test Name 1", results[0].HotelName);

        Assert.NotNull(results[1]);
        Assert.Equal("key2", results[1].HotelId);
        Assert.Equal("Test Name 2", results[1].HotelName);

        Assert.NotNull(results[2]);
        Assert.Equal("key3", results[2].HotelId);
        Assert.Equal("Test Name 3", results[2].HotelName);
    }

    [Fact]
    public async Task UpsertReturnsRecordKeyAsync()
    {
        // Arrange
        var hotel = new AzureCosmosDBNoSQLHotel("key") { HotelName = "Test Name" };

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act
        var result = await sut.UpsertAsync(hotel);

        // Assert
        Assert.Equal("key", result);

        this._mockContainer.Verify(l => l.UpsertItemAsync<JsonNode>(
            It.Is<JsonNode>(node =>
                node["id"]!.ToString() == "key" &&
                node["HotelName"]!.ToString() == "Test Name"),
            new PartitionKey("key"),
            It.IsAny<ItemRequestOptions>(),
            It.IsAny<CancellationToken>()),
            Times.Once());
    }

    [Fact]
    public async Task UpsertBatchReturnsRecordKeysAsync()
    {
        // Arrange
        var hotel1 = new AzureCosmosDBNoSQLHotel("key1") { HotelName = "Test Name 1" };
        var hotel2 = new AzureCosmosDBNoSQLHotel("key2") { HotelName = "Test Name 2" };
        var hotel3 = new AzureCosmosDBNoSQLHotel("key3") { HotelName = "Test Name 3" };

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act
        var results = await sut.UpsertAsync([hotel1, hotel2, hotel3]);

        // Assert
        Assert.NotNull(results);
        Assert.Equal(3, results.Count);

        Assert.Equal("key1", results[0]);
        Assert.Equal("key2", results[1]);
        Assert.Equal("key3", results[2]);
    }

    [Fact]
    public async Task VectorizedSearchReturnsValidRecordAsync()
    {
        // Arrange
        const string RecordKey = "key";
        const double ExpectedScore = 0.99;

        var jsonObject = new JsonObject
        {
            ["id"] = RecordKey,
            ["HotelName"] = "Test Name",
            ["SimilarityScore"] = ExpectedScore
        };

        var mockFeedResponse = new Mock<FeedResponse<JsonObject>>();
        mockFeedResponse
            .Setup(l => l.Resource)
            .Returns([jsonObject]);

        var mockFeedIterator = new Mock<FeedIterator<JsonObject>>();
        mockFeedIterator
            .SetupSequence(l => l.HasMoreResults)
            .Returns(true)
            .Returns(false);

        mockFeedIterator
            .Setup(l => l.ReadNextAsync(It.IsAny<CancellationToken>()))
            .ReturnsAsync(mockFeedResponse.Object);

        this._mockContainer
            .Setup(l => l.GetItemQueryIterator<JsonObject>(
                It.IsAny<QueryDefinition>(),
                It.IsAny<string>(),
                It.IsAny<QueryRequestOptions>()))
            .Returns(mockFeedIterator.Object);

        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act
        var results = await sut.SearchEmbeddingAsync(new ReadOnlyMemory<float>([1f, 2f, 3f]), top: 3).ToListAsync();
        var result = results[0];

        // Assert
        Assert.NotNull(result);
        Assert.Equal(RecordKey, result.Record.HotelId);
        Assert.Equal("Test Name", result.Record.HotelName);
        Assert.Equal(ExpectedScore, result.Score);
    }

    [Fact]
    public async Task VectorizedSearchWithUnsupportedVectorTypeThrowsExceptionAsync()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        // Act & Assert
        await Assert.ThrowsAsync<NotSupportedException>(async () =>
            await sut.SearchEmbeddingAsync(new List<double>([1, 2, 3]), top: 3).ToListAsync());
    }

    [Fact]
    public async Task VectorizedSearchWithNonExistentVectorPropertyNameThrowsExceptionAsync()
    {
        // Arrange
        var sut = new AzureCosmosDBNoSQLVectorStoreRecordCollection<string, AzureCosmosDBNoSQLHotel>(
            this._mockDatabase.Object,
            "collection");

        var searchOptions = new VectorSearchOptions<AzureCosmosDBNoSQLHotel> { VectorProperty = r => "non-existent-property" };

        // Act & Assert
        await Assert.ThrowsAsync<InvalidOperationException>(async () =>
            await sut.SearchEmbeddingAsync(new ReadOnlyMemory<float>([1f, 2f, 3f]), top: 3, searchOptions).ToListAsync());
    }

    public static TheoryData<List<string>, string, bool> CollectionExistsData => new()
    {
        { ["collection-2"], "collection-2", true },
        { [], "non-existent-collection", false }
    };

    public static TheoryData<List<string>, int> CreateCollectionIfNotExistsData => new()
    {
        { ["collection"], 0 },
        { [], 1 }
    };

    #region

    private bool VerifyContainerProperties(ContainerProperties expected, ContainerProperties actual)
    {
        Assert.Equal(expected.Id, actual.Id);
        Assert.Equal(expected.PartitionKeyPath, actual.PartitionKeyPath);
        Assert.Equal(expected.IndexingPolicy.IndexingMode, actual.IndexingPolicy.IndexingMode);
        Assert.Equal(expected.IndexingPolicy.Automatic, actual.IndexingPolicy.Automatic);

        if (expected.IndexingPolicy.IndexingMode != IndexingMode.None)
        {
            for (var i = 0; i < expected.VectorEmbeddingPolicy.Embeddings.Count; i++)
            {
                var expectedEmbedding = expected.VectorEmbeddingPolicy.Embeddings[i];
                var actualEmbedding = actual.VectorEmbeddingPolicy.Embeddings[i];

                Assert.Equal(expectedEmbedding.DataType, actualEmbedding.DataType);
                Assert.Equal(expectedEmbedding.Dimensions, actualEmbedding.Dimensions);
                Assert.Equal(expectedEmbedding.DistanceFunction, actualEmbedding.DistanceFunction);
                Assert.Equal(expectedEmbedding.Path, actualEmbedding.Path);
            }

            for (var i = 0; i < expected.IndexingPolicy.VectorIndexes.Count; i++)
            {
                var expectedIndexPath = expected.IndexingPolicy.VectorIndexes[i];
                var actualIndexPath = actual.IndexingPolicy.VectorIndexes[i];

                Assert.Equal(expectedIndexPath.Type, actualIndexPath.Type);
                Assert.Equal(expectedIndexPath.Path, actualIndexPath.Path);
            }

            for (var i = 0; i < expected.IndexingPolicy.IncludedPaths.Count; i++)
            {
                var expectedIncludedPath = expected.IndexingPolicy.IncludedPaths[i].Path;
                var actualIncludedPath = actual.IndexingPolicy.IncludedPaths[i].Path;

                Assert.Equal(expectedIncludedPath, actualIncludedPath);
            }

            for (var i = 0; i < expected.IndexingPolicy.ExcludedPaths.Count; i++)
            {
                var expectedExcludedPath = expected.IndexingPolicy.ExcludedPaths[i].Path;
                var actualExcludedPath = actual.IndexingPolicy.ExcludedPaths[i].Path;

                Assert.Equal(expectedExcludedPath, actualExcludedPath);
            }
        }

        return true;
    }

#pragma warning disable CA1812
    private sealed class TestModel
    {
        public string? Id { get; set; }

        public string? HotelName { get; set; }
    }

    private sealed class TestIndexingModel
    {
        [VectorStoreRecordKey]
        public string? Id { get; set; }

        [VectorStoreRecordVector(Dimensions: 2, DistanceFunction = DistanceFunction.CosineSimilarity, IndexKind = IndexKind.Flat)]
        public ReadOnlyMemory<float>? DescriptionEmbedding2 { get; set; }

        [VectorStoreRecordVector(Dimensions: 3, DistanceFunction = DistanceFunction.DotProductSimilarity, IndexKind = IndexKind.QuantizedFlat)]
        public ReadOnlyMemory<byte>? DescriptionEmbedding3 { get; set; }

        [VectorStoreRecordVector(Dimensions: 4, DistanceFunction = DistanceFunction.EuclideanDistance, IndexKind = IndexKind.DiskAnn)]
        public ReadOnlyMemory<sbyte>? DescriptionEmbedding4 { get; set; }

        [VectorStoreRecordData(IsIndexed = true)]
        public string? IndexableData1 { get; set; }

        [VectorStoreRecordData(IsFullTextIndexed = true)]
        public string? IndexableData2 { get; set; }

        [VectorStoreRecordData]
        public string? NonIndexableData1 { get; set; }
    }
#pragma warning restore CA1812

    #endregion
}
