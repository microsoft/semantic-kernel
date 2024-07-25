// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Nodes;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.SemanticKernel.Data;
using Moq;
using NRedisStack;
using StackExchange.Redis;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisJsonVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
public class RedisJsonVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";
    private const string TestRecordKey1 = "testid1";
    private const string TestRecordKey2 = "testid2";

    private readonly Mock<IDatabase> _redisDatabaseMock;

    public RedisJsonVectorStoreRecordCollectionTests()
    {
        this._redisDatabaseMock = new Mock<IDatabase>(MockBehavior.Strict);

        var batchMock = new Mock<IBatch>();
        this._redisDatabaseMock.Setup(x => x.CreateBatch(It.IsAny<object>())).Returns(batchMock.Object);
    }

    [Theory]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange
        if (expectedExists)
        {
            SetupExecuteMock(this._redisDatabaseMock, ["index_name", collectionName]);
        }
        else
        {
            SetupExecuteMock(this._redisDatabaseMock, new RedisServerException("Unknown index name"));
        }
        var sut = new RedisJsonVectorStoreRecordCollection<SinglePropsModel>(
            this._redisDatabaseMock.Object,
            collectionName);

        // Act
        var actual = await sut.CollectionExistsAsync();

        // Assert
        var expectedArgs = new object[] { collectionName };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "FT.INFO",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);
        Assert.Equal(expectedExists, actual);
    }

    [Fact]
    public async Task CanCreateCollectionAsync()
    {
        // Arrange.
        SetupExecuteMock(this._redisDatabaseMock, string.Empty);
        var sut = new RedisJsonVectorStoreRecordCollection<SinglePropsModel>(this._redisDatabaseMock.Object, TestCollectionName);

        // Act.
        await sut.CreateCollectionAsync();

        // Assert.
        var expectedArgs = new object[] {
            "testcollection",
            "ON",
            "JSON",
            "PREFIX",
            1,
            "testcollection:",
            "SCHEMA",
            "$.OriginalNameData",
            "AS",
            "OriginalNameData",
            "TEXT",
            "$.data_json_name",
            "AS",
            "data_json_name",
            "TEXT",
            "$.vector_json_name",
            "AS",
            "vector_json_name",
            "VECTOR",
            "HNSW",
            6,
            "TYPE",
            "FLOAT32",
            "DIM",
            "4",
            "DISTANCE_METRIC",
            "COSINE" };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "FT.CREATE",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);
    }

    [Fact]
    public async Task CanDeleteCollectionAsync()
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, string.Empty);
        var sut = this.CreateRecordCollection(false);

        // Act
        await sut.DeleteCollectionAsync();

        // Assert
        var expectedArgs = new object[] { TestCollectionName };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "FT.DROPINDEX",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetRecordWithVectorsAsync(bool useDefinition)
    {
        // Arrange
        var redisResultString = """{ "OriginalNameData": "data 1", "data_json_name": "data 1", "vector_json_name": [1, 2, 3, 4] }""";
        SetupExecuteMock(this._redisDatabaseMock, redisResultString);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = true });

        // Assert
        var expectedArgs = new object[] { TestRecordKey1 };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.GET",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);

        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.OriginalNameData);
        Assert.Equal("data 1", actual.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetRecordWithoutVectorsAsync(bool useDefinition)
    {
        // Arrange
        var redisResultString = """{ "OriginalNameData": "data 1", "data_json_name": "data 1" }""";
        SetupExecuteMock(this._redisDatabaseMock, redisResultString);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = false });

        // Assert
        var expectedArgs = new object[] { TestRecordKey1, "OriginalNameData", "data_json_name" };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.GET",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);

        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.OriginalNameData);
        Assert.Equal("data 1", actual.Data);
        Assert.False(actual.Vector.HasValue);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetManyRecordsWithVectorsAsync(bool useDefinition)
    {
        // Arrange
        var redisResultString1 = """{ "OriginalNameData": "data 1", "data_json_name": "data 1", "vector_json_name": [1, 2, 3, 4] }""";
        var redisResultString2 = """{ "OriginalNameData": "data 2", "data_json_name": "data 2", "vector_json_name": [5, 6, 7, 8] }""";
        SetupExecuteMock(this._redisDatabaseMock, [redisResultString1, redisResultString2]);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        var actual = await sut.GetBatchAsync(
            [TestRecordKey1, TestRecordKey2],
            new() { IncludeVectors = true }).ToListAsync();

        // Assert
        var expectedArgs = new object[] { TestRecordKey1, TestRecordKey2, "$" };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.MGET",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);

        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0].Key);
        Assert.Equal("data 1", actual[0].OriginalNameData);
        Assert.Equal("data 1", actual[0].Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual[0].Vector!.Value.ToArray());
        Assert.Equal(TestRecordKey2, actual[1].Key);
        Assert.Equal("data 2", actual[1].OriginalNameData);
        Assert.Equal("data 2", actual[1].Data);
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual[1].Vector!.Value.ToArray());
    }

    [Fact]
    public async Task CanGetRecordWithCustomMapperAsync()
    {
        // Arrange.
        var redisResultString = """{ "OriginalNameData": "data 1", "data_json_name": "data 1", "vector_json_name": [1, 2, 3, 4] }""";
        SetupExecuteMock(this._redisDatabaseMock, redisResultString);

        // Arrange mapper mock from JsonNode to data model.
        var mapperMock = new Mock<IVectorStoreRecordMapper<SinglePropsModel, (string key, JsonNode node)>>(MockBehavior.Strict);
        mapperMock.Setup(
            x => x.MapFromStorageToDataModel(
                It.IsAny<(string key, JsonNode node)>(),
                It.IsAny<StorageToDataModelMapperOptions>()))
            .Returns(CreateModel(TestRecordKey1, true));

        // Arrange target with custom mapper.
        var sut = new RedisJsonVectorStoreRecordCollection<SinglePropsModel>(
            this._redisDatabaseMock.Object,
            TestCollectionName,
            new()
            {
                JsonNodeCustomMapper = mapperMock.Object
            });

        // Act
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = true });

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.OriginalNameData);
        Assert.Equal("data 1", actual.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());

        mapperMock
            .Verify(
                x => x.MapFromStorageToDataModel(
                    It.Is<(string key, JsonNode node)>(x => x.key == TestRecordKey1),
                    It.Is<StorageToDataModelMapperOptions>(x => x.IncludeVectors)),
                Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanDeleteRecordAsync(bool useDefinition)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, "200");
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        await sut.DeleteAsync(TestRecordKey1);

        // Assert
        var expectedArgs = new object[] { TestRecordKey1 };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.DEL",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanDeleteManyRecordsWithVectorsAsync(bool useDefinition)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, "200");
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        await sut.DeleteBatchAsync([TestRecordKey1, TestRecordKey2]);

        // Assert
        var expectedArgs1 = new object[] { TestRecordKey1 };
        var expectedArgs2 = new object[] { TestRecordKey2 };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.DEL",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs1))),
                Times.Once);
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.DEL",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs2))),
                Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanUpsertRecordAsync(bool useDefinition)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, "OK");
        var sut = this.CreateRecordCollection(useDefinition);
        var model = CreateModel(TestRecordKey1, true);

        // Act
        await sut.UpsertAsync(model);

        // Assert
        // TODO: Fix issue where NotAnnotated is being included in the JSON.
        var expectedArgs = new object[] { TestRecordKey1, "$", """{"OriginalNameData":"data 1","data_json_name":"data 1","vector_json_name":[1,2,3,4],"NotAnnotated":null}""" };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.SET",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanUpsertManyRecordsAsync(bool useDefinition)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, "OK");
        var sut = this.CreateRecordCollection(useDefinition);

        var model1 = CreateModel(TestRecordKey1, true);
        var model2 = CreateModel(TestRecordKey2, true);

        // Act
        var actual = await sut.UpsertBatchAsync([model1, model2]).ToListAsync();

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0]);
        Assert.Equal(TestRecordKey2, actual[1]);

        // TODO: Fix issue where NotAnnotated is being included in the JSON.
        var expectedArgs = new object[] { TestRecordKey1, "$", """{"OriginalNameData":"data 1","data_json_name":"data 1","vector_json_name":[1,2,3,4],"NotAnnotated":null}""", TestRecordKey2, "$", """{"OriginalNameData":"data 1","data_json_name":"data 1","vector_json_name":[1,2,3,4],"NotAnnotated":null}""" };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.MSET",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);
    }

    [Fact]
    public async Task CanUpsertRecordWithCustomMapperAsync()
    {
        // Arrange.
        SetupExecuteMock(this._redisDatabaseMock, "OK");

        // Arrange mapper mock from data model to JsonNode.
        var mapperMock = new Mock<IVectorStoreRecordMapper<SinglePropsModel, (string key, JsonNode node)>>(MockBehavior.Strict);
        var jsonNode = """{"OriginalNameData": "data 1", "data_json_name":"data 1","vector_json_name":[1,2,3,4],"NotAnnotated":null}""";
        mapperMock
            .Setup(x => x.MapFromDataToStorageModel(It.IsAny<SinglePropsModel>()))
            .Returns((TestRecordKey1, JsonNode.Parse(jsonNode)!));

        // Arrange target with custom mapper.
        var sut = new RedisJsonVectorStoreRecordCollection<SinglePropsModel>(
            this._redisDatabaseMock.Object,
            TestCollectionName,
            new()
            {
                JsonNodeCustomMapper = mapperMock.Object
            });

        var model = CreateModel(TestRecordKey1, true);

        // Act
        await sut.UpsertAsync(model);

        // Assert
        mapperMock
            .Verify(
                x => x.MapFromDataToStorageModel(It.Is<SinglePropsModel>(x => x == model)),
                Times.Once);
    }

    private RedisJsonVectorStoreRecordCollection<SinglePropsModel> CreateRecordCollection(bool useDefinition)
    {
        return new RedisJsonVectorStoreRecordCollection<SinglePropsModel>(
            this._redisDatabaseMock.Object,
            TestCollectionName,
            new()
            {
                PrefixCollectionNameToKeyNames = false,
                VectorStoreRecordDefinition = useDefinition ? this._singlePropsDefinition : null
            });
    }

    private static void SetupExecuteMock(Mock<IDatabase> redisDatabaseMock, Exception exception)
    {
        redisDatabaseMock
            .Setup(
                x => x.ExecuteAsync(
                    It.IsAny<string>(),
                    It.IsAny<object[]>()))
            .ThrowsAsync(exception);
    }

    private static void SetupExecuteMock(Mock<IDatabase> redisDatabaseMock, IEnumerable<string> redisResultStrings)
    {
        var results = redisResultStrings
            .Select(x => RedisResult.Create(new RedisValue(x)))
            .ToArray();
        redisDatabaseMock
            .Setup(
                x => x.ExecuteAsync(
                    It.IsAny<string>(),
                    It.IsAny<object[]>()))
            .ReturnsAsync(RedisResult.Create(results));
    }

    private static void SetupExecuteMock(Mock<IDatabase> redisDatabaseMock, string redisResultString)
    {
        redisDatabaseMock
            .Setup(
                x => x.ExecuteAsync(
                    It.IsAny<string>(),
                    It.IsAny<object[]>()))
            .Callback((string command, object[] args) =>
            {
                Console.WriteLine(args);
            })
            .ReturnsAsync(RedisResult.Create(new RedisValue(redisResultString)));
    }

    private static SinglePropsModel CreateModel(string key, bool withVectors)
    {
        return new SinglePropsModel
        {
            Key = key,
            OriginalNameData = "data 1",
            Data = "data 1",
            Vector = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            NotAnnotated = null,
        };
    }

    private readonly VectorStoreRecordDefinition _singlePropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key"),
            new VectorStoreRecordDataProperty("OriginalNameData"),
            new VectorStoreRecordDataProperty("Data") { StoragePropertyName = "ignored_data_json_name" },
            new VectorStoreRecordVectorProperty("Vector")
        ]
    };

    public sealed class SinglePropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData(IsFilterable = true)]
        public string OriginalNameData { get; set; } = string.Empty;

        [JsonPropertyName("data_json_name")]
        [VectorStoreRecordData(IsFilterable = true, StoragePropertyName = "ignored_data_json_name")]
        public string Data { get; set; } = string.Empty;

        [JsonPropertyName("vector_json_name")]
        [VectorStoreRecordVector(4, StoragePropertyName = "ignored_vector_storage_name")]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
