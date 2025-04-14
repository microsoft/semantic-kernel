// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using NRedisStack;
using StackExchange.Redis;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

#pragma warning disable CS0618 // VectorSearchFilter is obsolete

/// <summary>
/// Contains tests for the <see cref="RedisJsonVectorStoreRecordCollection{TKey, TRecord}"/> class.
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
        this._redisDatabaseMock.Setup(l => l.Database).Returns(0);

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
        var sut = new RedisJsonVectorStoreRecordCollection<string, MultiPropsModel>(
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

    [Theory]
    [InlineData(true, true, "data2", "vector2")]
    [InlineData(true, false, "Data2", "Vector2")]
    [InlineData(false, true, "data2", "vector2")]
    [InlineData(false, false, "Data2", "Vector2")]
    public async Task CanCreateCollectionAsync(bool useDefinition, bool useCustomJsonSerializerOptions, string expectedData2Name, string expectedVector2Name)
    {
        // Arrange.
        SetupExecuteMock(this._redisDatabaseMock, string.Empty);
        var sut = this.CreateRecordCollection(useDefinition, useCustomJsonSerializerOptions);

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
            "$.data1_json_name",
            "AS",
            "data1_json_name",
            "TAG",
            $"$.{expectedData2Name}",
            "AS",
            expectedData2Name,
            "TAG",
            "$.vector1_json_name",
            "AS",
            "vector1_json_name",
            "VECTOR",
            "HNSW",
            6,
            "TYPE",
            "FLOAT32",
            "DIM",
            "4",
            "DISTANCE_METRIC",
            "COSINE",
            $"$.{expectedVector2Name}",
            "AS",
            expectedVector2Name,
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
    [InlineData(true, true, """{ "data1_json_name": "data 1", "data2": "data 2", "vector1_json_name": [1, 2, 3, 4], "vector2": [1, 2, 3, 4] }""")]
    [InlineData(true, false, """{ "data1_json_name": "data 1", "Data2": "data 2", "vector1_json_name": [1, 2, 3, 4], "Vector2": [1, 2, 3, 4] }""")]
    [InlineData(false, true, """{ "data1_json_name": "data 1", "data2": "data 2", "vector1_json_name": [1, 2, 3, 4], "vector2": [1, 2, 3, 4] }""")]
    [InlineData(false, false, """{ "data1_json_name": "data 1", "Data2": "data 2", "vector1_json_name": [1, 2, 3, 4], "Vector2": [1, 2, 3, 4] }""")]
    public async Task CanGetRecordWithVectorsAsync(bool useDefinition, bool useCustomJsonSerializerOptions, string redisResultString)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, redisResultString);
        var sut = this.CreateRecordCollection(useDefinition, useCustomJsonSerializerOptions);

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
        Assert.Equal("data 1", actual.Data1);
        Assert.Equal("data 2", actual.Data2);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector1!.Value.ToArray());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector2!.Value.ToArray());
    }

    [Theory]
    [InlineData(true, true, """{ "data1_json_name": "data 1", "data2": "data 2" }""", "data2")]
    [InlineData(true, false, """{ "data1_json_name": "data 1", "Data2": "data 2" }""", "Data2")]
    [InlineData(false, true, """{ "data1_json_name": "data 1", "data2": "data 2" }""", "data2")]
    [InlineData(false, false, """{ "data1_json_name": "data 1", "Data2": "data 2" }""", "Data2")]
    public async Task CanGetRecordWithoutVectorsAsync(bool useDefinition, bool useCustomJsonSerializerOptions, string redisResultString, string expectedData2Name)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, redisResultString);
        var sut = this.CreateRecordCollection(useDefinition, useCustomJsonSerializerOptions);

        // Act
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = false });

        // Assert
        var expectedArgs = new object[] { TestRecordKey1, "data1_json_name", expectedData2Name };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.GET",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);

        Assert.NotNull(actual);
        Assert.Equal(TestRecordKey1, actual.Key);
        Assert.Equal("data 1", actual.Data1);
        Assert.Equal("data 2", actual.Data2);
        Assert.False(actual.Vector1.HasValue);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanGetManyRecordsWithVectorsAsync(bool useDefinition)
    {
        // Arrange
        var redisResultString1 = """{ "data1_json_name": "data 1", "Data2": "data 2", "vector1_json_name": [1, 2, 3, 4], "Vector2": [1, 2, 3, 4] }""";
        var redisResultString2 = """{ "data1_json_name": "data 1", "Data2": "data 2", "vector1_json_name": [5, 6, 7, 8], "Vector2": [1, 2, 3, 4] }""";
        SetupExecuteMock(this._redisDatabaseMock, [redisResultString1, redisResultString2]);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        var actual = await sut.GetAsync(
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
        Assert.Equal("data 1", actual[0].Data1);
        Assert.Equal("data 2", actual[0].Data2);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual[0].Vector1!.Value.ToArray());
        Assert.Equal(TestRecordKey2, actual[1].Key);
        Assert.Equal("data 1", actual[1].Data1);
        Assert.Equal("data 2", actual[1].Data2);
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual[1].Vector1!.Value.ToArray());
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
        await sut.DeleteAsync([TestRecordKey1, TestRecordKey2]);

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
    [InlineData(true, true, """{"data1_json_name":"data 1","data2":"data 2","vector1_json_name":[1,2,3,4],"vector2":[1,2,3,4],"notAnnotated":null}""")]
    [InlineData(true, false, """{"data1_json_name":"data 1","Data2":"data 2","vector1_json_name":[1,2,3,4],"Vector2":[1,2,3,4],"NotAnnotated":null}""")]
    [InlineData(false, true, """{"data1_json_name":"data 1","data2":"data 2","vector1_json_name":[1,2,3,4],"vector2":[1,2,3,4],"notAnnotated":null}""")]
    [InlineData(false, false, """{"data1_json_name":"data 1","Data2":"data 2","vector1_json_name":[1,2,3,4],"Vector2":[1,2,3,4],"NotAnnotated":null}""")]
    public async Task CanUpsertRecordAsync(bool useDefinition, bool useCustomJsonSerializerOptions, string expectedUpsertedJson)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, "OK");
        var sut = this.CreateRecordCollection(useDefinition, useCustomJsonSerializerOptions);
        var model = CreateModel(TestRecordKey1, true);

        // Act
        await sut.UpsertAsync(model);

        // Assert
        // TODO: Fix issue where NotAnnotated is being included in the JSON.
        var expectedArgs = new object[] { TestRecordKey1, "$", expectedUpsertedJson };
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
        var actual = await sut.UpsertAsync([model1, model2]);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(TestRecordKey1, actual[0]);
        Assert.Equal(TestRecordKey2, actual[1]);

        // TODO: Fix issue where NotAnnotated is being included in the JSON.
        var expectedArgs = new object[] { TestRecordKey1, "$", """{"data1_json_name":"data 1","Data2":"data 2","vector1_json_name":[1,2,3,4],"Vector2":[1,2,3,4],"NotAnnotated":null}""", TestRecordKey2, "$", """{"data1_json_name":"data 1","Data2":"data 2","vector1_json_name":[1,2,3,4],"Vector2":[1,2,3,4],"NotAnnotated":null}""" };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "JSON.MSET",
                    It.Is<object[]>(x => x.SequenceEqual(expectedArgs))),
                Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanSearchWithVectorAndFilterAsync(bool useDefinition)
    {
        // Arrange
        var jsonResult = """{ "data1_json_name": "data 1", "Data2": "data 2", "vector1_json_name": [1, 2, 3, 4], "Vector2": [1, 2, 3, 4] }""";
        SetupExecuteMock(this._redisDatabaseMock, new RedisResult[]
        {
            RedisResult.Create(new RedisValue("1")),
            RedisResult.Create(new RedisValue(TestRecordKey1)),
            RedisResult.Create(new RedisValue("0.8")),
            RedisResult.Create(
            [
                new RedisValue("$"),
                new RedisValue(jsonResult),
                new RedisValue("vector_score"),
                new RedisValue("0.25")
            ]),
        });
        var sut = this.CreateRecordCollection(useDefinition);

        var filter = new VectorSearchFilter().EqualTo(nameof(MultiPropsModel.Data1), "data 1");

        // Act.
        var results = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new[] { 1f, 2f, 3f, 4f }),
            top: 5,
            new()
            {
                IncludeVectors = true,
                OldFilter = filter,
                VectorProperty = r => r.Vector1,
                Skip = 2
            }).ToListAsync();

        // Assert.
        var expectedArgs = new object[]
        {
            "testcollection",
            "(@data1_json_name:{data 1})=>[KNN 7 @vector1_json_name $embedding AS vector_score]",
            "WITHSCORES",
            "SORTBY",
            "vector_score",
            "LIMIT",
            2,
            7,
            "PARAMS",
            2,
            "embedding",
            MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 1, 2, 3, 4 })).ToArray(),
            "DIALECT",
            2
        };
        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "FT.SEARCH",
                    It.Is<object[]>(x => x.Where(y => !(y is byte[])).SequenceEqual(expectedArgs.Where(y => !(y is byte[]))))),
                Times.Once);

        Assert.Single(results);
        Assert.Equal(TestRecordKey1, results.First().Record.Key);
        Assert.Equal(0.25d, results.First().Score);
        Assert.Equal("data 1", results.First().Record.Data1);
        Assert.Equal("data 2", results.First().Record.Data2);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, results.First().Record.Vector1!.Value.ToArray());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, results.First().Record.Vector2!.Value.ToArray());
    }

    private RedisJsonVectorStoreRecordCollection<string, MultiPropsModel> CreateRecordCollection(bool useDefinition, bool useCustomJsonSerializerOptions = false)
    {
        return new RedisJsonVectorStoreRecordCollection<string, MultiPropsModel>(
            this._redisDatabaseMock.Object,
            TestCollectionName,
            new()
            {
                PrefixCollectionNameToKeyNames = false,
                VectorStoreRecordDefinition = useDefinition ? this._multiPropsDefinition : null,
                JsonSerializerOptions = useCustomJsonSerializerOptions ? this._customJsonSerializerOptions : null
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

    private static void SetupExecuteMock(Mock<IDatabase> redisDatabaseMock, IEnumerable<RedisResult> redisResultStrings)
    {
        var results = redisResultStrings
            .Select(x => x)
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

    private static MultiPropsModel CreateModel(string key, bool withVectors)
    {
        return new MultiPropsModel
        {
            Key = key,
            Data1 = "data 1",
            Data2 = "data 2",
            Vector1 = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            Vector2 = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            NotAnnotated = null,
        };
    }

    private readonly JsonSerializerOptions _customJsonSerializerOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase
    };

    private readonly VectorStoreRecordDefinition _multiPropsDefinition = new()
    {
        Properties =
        [
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("Data1", typeof(string)) { IsIndexed = true, StoragePropertyName = "ignored_data1_storage_name" },
            new VectorStoreRecordDataProperty("Data2", typeof(string)) { IsIndexed = true },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>), 4) { DistanceFunction = DistanceFunction.CosineDistance, StoragePropertyName = "ignored_vector1_storage_name" },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>), 4)
        ]
    };

    public sealed class MultiPropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [JsonPropertyName("data1_json_name")]
        [VectorStoreRecordData(IsIndexed = true, StoragePropertyName = "ignored_data1_storage_name")]
        public string Data1 { get; set; } = string.Empty;

        [VectorStoreRecordData(IsIndexed = true)]
        public string Data2 { get; set; } = string.Empty;

        [JsonPropertyName("vector1_json_name")]
        [VectorStoreRecordVector(4, DistanceFunction = DistanceFunction.CosineDistance, StoragePropertyName = "ignored_vector1_storage_name")]
        public ReadOnlyMemory<float>? Vector1 { get; set; }

        [VectorStoreRecordVector(4)]
        public ReadOnlyMemory<float>? Vector2 { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
