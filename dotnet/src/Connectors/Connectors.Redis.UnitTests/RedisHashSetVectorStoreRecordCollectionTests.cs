// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json.Serialization;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using NRedisStack;
using StackExchange.Redis;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisHashSetVectorStoreRecordCollection{TRecord}"/> class.
/// </summary>
public class RedisHashSetVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";
    private const string TestRecordKey1 = "testid1";
    private const string TestRecordKey2 = "testid2";

    private readonly Mock<IDatabase> _redisDatabaseMock;

    public RedisHashSetVectorStoreRecordCollectionTests()
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
        var sut = new RedisHashSetVectorStoreRecordCollection<SinglePropsModel>(
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
        var sut = new RedisHashSetVectorStoreRecordCollection<SinglePropsModel>(this._redisDatabaseMock.Object, TestCollectionName);

        // Act.
        await sut.CreateCollectionAsync();

        // Assert.
        var expectedArgs = new object[] {
            "testcollection",
            "PREFIX",
            1,
            "testcollection:",
            "SCHEMA",
            "OriginalNameData",
            "AS",
            "OriginalNameData",
            "TAG",
            "data_storage_name",
            "AS",
            "data_storage_name",
            "TAG",
            "vector_storage_name",
            "AS",
            "vector_storage_name",
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
        var hashEntries = new HashEntry[]
        {
            new("OriginalNameData", "data 1"),
            new("data_storage_name", "data 1"),
            new("vector_storage_name", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 1, 2, 3, 4 })).ToArray())
        };
        this._redisDatabaseMock.Setup(x => x.HashGetAllAsync(It.IsAny<RedisKey>(), CommandFlags.None)).ReturnsAsync(hashEntries);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = true });

        // Assert
        this._redisDatabaseMock.Verify(x => x.HashGetAllAsync(TestRecordKey1, CommandFlags.None), Times.Once);

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
        var redisValues = new RedisValue[] { new("data 1"), new("data 1") };
        this._redisDatabaseMock.Setup(x => x.HashGetAsync(It.IsAny<RedisKey>(), It.IsAny<RedisValue[]>(), CommandFlags.None)).ReturnsAsync(redisValues);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        var actual = await sut.GetAsync(
            TestRecordKey1,
            new() { IncludeVectors = false });

        // Assert
        var fieldNames = new RedisValue[] { "OriginalNameData", "data_storage_name" };
        this._redisDatabaseMock.Verify(x => x.HashGetAsync(TestRecordKey1, fieldNames, CommandFlags.None), Times.Once);

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
        var hashEntries1 = new HashEntry[]
        {
            new("OriginalNameData", "data 1"),
            new("data_storage_name", "data 1"),
            new("vector_storage_name", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 1, 2, 3, 4 })).ToArray())
        };
        var hashEntries2 = new HashEntry[]
        {
            new("OriginalNameData", "data 2"),
            new("data_storage_name", "data 2"),
            new("vector_storage_name", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 5, 6, 7, 8 })).ToArray())
        };
        this._redisDatabaseMock.Setup(x => x.HashGetAllAsync(It.IsAny<RedisKey>(), CommandFlags.None)).Returns((RedisKey key, CommandFlags flags) =>
        {
            return key switch
            {
                RedisKey k when k == TestRecordKey1 => Task.FromResult(hashEntries1),
                RedisKey k when k == TestRecordKey2 => Task.FromResult(hashEntries2),
                _ => throw new ArgumentException("Unexpected key."),
            };
        });
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        var actual = await sut.GetBatchAsync(
            [TestRecordKey1, TestRecordKey2],
            new() { IncludeVectors = true }).ToListAsync();

        // Assert
        this._redisDatabaseMock.Verify(x => x.HashGetAllAsync(TestRecordKey1, CommandFlags.None), Times.Once);
        this._redisDatabaseMock.Verify(x => x.HashGetAllAsync(TestRecordKey2, CommandFlags.None), Times.Once);

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
        var hashEntries = new HashEntry[]
        {
            new("OriginalNameData", "data 1"),
            new("data_storage_name", "data 1"),
            new("vector_storage_name", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 1, 2, 3, 4 })).ToArray())
        };
        this._redisDatabaseMock.Setup(x => x.HashGetAllAsync(It.IsAny<RedisKey>(), CommandFlags.None)).ReturnsAsync(hashEntries);

        // Arrange mapper mock from JsonNode to data model.
        var mapperMock = new Mock<IVectorStoreRecordMapper<SinglePropsModel, (string key, HashEntry[] hashEntries)>>(MockBehavior.Strict);
        mapperMock.Setup(
            x => x.MapFromStorageToDataModel(
                It.IsAny<(string key, HashEntry[] hashEntries)>(),
                It.IsAny<StorageToDataModelMapperOptions>()))
            .Returns(CreateModel(TestRecordKey1, true));

        // Arrange target with custom mapper.
        var sut = new RedisHashSetVectorStoreRecordCollection<SinglePropsModel>(
            this._redisDatabaseMock.Object,
            TestCollectionName,
            new()
            {
                HashEntriesCustomMapper = mapperMock.Object
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
                    It.Is<(string key, HashEntry[] hashEntries)>(x => x.key == TestRecordKey1),
                    It.Is<StorageToDataModelMapperOptions>(x => x.IncludeVectors)),
                Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanDeleteRecordAsync(bool useDefinition)
    {
        // Arrange
        this._redisDatabaseMock.Setup(x => x.KeyDeleteAsync(It.IsAny<RedisKey>(), CommandFlags.None)).ReturnsAsync(true);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        await sut.DeleteAsync(TestRecordKey1);

        // Assert
        this._redisDatabaseMock.Verify(x => x.KeyDeleteAsync(TestRecordKey1, CommandFlags.None), Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanDeleteManyRecordsWithVectorsAsync(bool useDefinition)
    {
        // Arrange
        this._redisDatabaseMock.Setup(x => x.KeyDeleteAsync(It.IsAny<RedisKey>(), CommandFlags.None)).ReturnsAsync(true);
        var sut = this.CreateRecordCollection(useDefinition);

        // Act
        await sut.DeleteBatchAsync([TestRecordKey1, TestRecordKey2]);

        // Assert
        this._redisDatabaseMock.Verify(x => x.KeyDeleteAsync(TestRecordKey1, CommandFlags.None), Times.Once);
        this._redisDatabaseMock.Verify(x => x.KeyDeleteAsync(TestRecordKey2, CommandFlags.None), Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanUpsertRecordAsync(bool useDefinition)
    {
        // Arrange
        this._redisDatabaseMock.Setup(x => x.HashSetAsync(It.IsAny<RedisKey>(), It.IsAny<HashEntry[]>(), CommandFlags.None)).Returns(Task.CompletedTask);
        var sut = this.CreateRecordCollection(useDefinition);
        var model = CreateModel(TestRecordKey1, true);

        // Act
        await sut.UpsertAsync(model);

        // Assert
        this._redisDatabaseMock.Verify(
            x => x.HashSetAsync(
                TestRecordKey1,
                It.Is<HashEntry[]>(x => x.Length == 3 && x[0].Name == "OriginalNameData" && x[1].Name == "data_storage_name" && x[2].Name == "vector_storage_name"),
                CommandFlags.None),
            Times.Once);
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public async Task CanUpsertManyRecordsAsync(bool useDefinition)
    {
        // Arrange
        this._redisDatabaseMock.Setup(x => x.HashSetAsync(It.IsAny<RedisKey>(), It.IsAny<HashEntry[]>(), CommandFlags.None)).Returns(Task.CompletedTask);
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

        this._redisDatabaseMock.Verify(
            x => x.HashSetAsync(
                TestRecordKey1,
                It.Is<HashEntry[]>(x => x.Length == 3 && x[0].Name == "OriginalNameData" && x[1].Name == "data_storage_name" && x[2].Name == "vector_storage_name"),
                CommandFlags.None),
            Times.Once);
        this._redisDatabaseMock.Verify(
            x => x.HashSetAsync(
                TestRecordKey2,
                It.Is<HashEntry[]>(x => x.Length == 3 && x[0].Name == "OriginalNameData" && x[1].Name == "data_storage_name" && x[2].Name == "vector_storage_name"),
                CommandFlags.None),
            Times.Once);
    }

    [Fact]
    public async Task CanUpsertRecordWithCustomMapperAsync()
    {
        // Arrange.
        this._redisDatabaseMock.Setup(x => x.HashSetAsync(It.IsAny<RedisKey>(), It.IsAny<HashEntry[]>(), CommandFlags.None)).Returns(Task.CompletedTask);

        // Arrange mapper mock from data model to JsonNode.
        var mapperMock = new Mock<IVectorStoreRecordMapper<SinglePropsModel, (string key, HashEntry[] hashEntries)>>(MockBehavior.Strict);
        var hashEntries = new HashEntry[]
        {
            new("OriginalNameData", "data 1"),
            new("data_storage_name", "data 1"),
            new("vector_storage_name", "[1,2,3,4]"),
            new("NotAnnotated", RedisValue.Null)
        };
        mapperMock
            .Setup(x => x.MapFromDataToStorageModel(It.IsAny<SinglePropsModel>()))
            .Returns((TestRecordKey1, hashEntries));

        // Arrange target with custom mapper.
        var sut = new RedisHashSetVectorStoreRecordCollection<SinglePropsModel>(
            this._redisDatabaseMock.Object,
            TestCollectionName,
            new()
            {
                HashEntriesCustomMapper = mapperMock.Object
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

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanSearchWithVectorAndFilterAsync(bool useDefinition, bool includeVectors)
    {
        // Arrange
        SetupExecuteMock(this._redisDatabaseMock, new RedisResult[]
        {
            RedisResult.Create(new RedisValue("1")),
            RedisResult.Create(new RedisValue(TestRecordKey1)),
            RedisResult.Create(new RedisValue("0.8")),
            RedisResult.Create(
            [
                new RedisValue("OriginalNameData"),
                new RedisValue("original data 1"),
                new RedisValue("data_storage_name"),
                new RedisValue("data 1"),
                new RedisValue("vector_storage_name"),
                RedisValue.Unbox(MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 1, 2, 3, 4 })).ToArray()),
                new RedisValue("vector_score"),
                new RedisValue("0.25"),
            ]),
        });
        var sut = this.CreateRecordCollection(useDefinition);

        var filter = new VectorSearchFilter().EqualTo(nameof(SinglePropsModel.Data), "data 1");

        // Act.
        var actual = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new[] { 1f, 2f, 3f, 4f }),
            new()
            {
                IncludeVectors = includeVectors,
                OldFilter = filter,
                Top = 5,
                Skip = 2
            });

        // Assert.
        var expectedArgsPart1 = new object[]
        {
            "testcollection",
            "(@data_storage_name:{data 1})=>[KNN 7 @vector_storage_name $embedding AS vector_score]",
            "WITHSCORES",
            "SORTBY",
            "vector_score",
            "LIMIT",
            2,
            7
        };
        var returnArgs = includeVectors ? Array.Empty<object>() : new object[]
        {
            "RETURN",
            3,
            "OriginalNameData",
            "data_storage_name",
            "vector_score"
        };
        var expectedArgsPart2 = new object[]
        {
            "PARAMS",
            2,
            "embedding",
            MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 1, 2, 3, 4 })).ToArray(),
            "DIALECT",
            2
        };
        var expectedArgs = expectedArgsPart1.Concat(returnArgs).Concat(expectedArgsPart2).ToArray();

        this._redisDatabaseMock
            .Verify(
                x => x.ExecuteAsync(
                    "FT.SEARCH",
                    It.Is<object[]>(x => x.Where(y => !(y is byte[])).SequenceEqual(expectedArgs.Where(y => !(y is byte[]))))),
                Times.Once);

        var results = await actual.Results.ToListAsync();
        Assert.Single(results);
        Assert.Equal(TestRecordKey1, results.First().Record.Key);
        Assert.Equal(0.25d, results.First().Score);
        Assert.Equal("original data 1", results.First().Record.OriginalNameData);
        Assert.Equal("data 1", results.First().Record.Data);
        if (includeVectors)
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, results.First().Record.Vector!.Value.ToArray());
        }
        else
        {
            Assert.False(results.First().Record.Vector.HasValue);
        }
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

    /// <summary>
    /// Tests that the collection can be created even if the definition and the type do not match.
    /// In this case, the expectation is that a custom mapper will be provided to map between the
    /// schema as defined by the definition and the different data model.
    /// </summary>
    [Fact]
    public void CanCreateCollectionWithMismatchedDefinitionAndType()
    {
        // Arrange.
        var definition = new VectorStoreRecordDefinition()
        {
            Properties = new List<VectorStoreRecordProperty>
            {
                new VectorStoreRecordKeyProperty("Id", typeof(string)),
                new VectorStoreRecordDataProperty("Text", typeof(string)),
                new VectorStoreRecordVectorProperty("Embedding", typeof(ReadOnlyMemory<float>)) { Dimensions = 4 },
            }
        };

        // Act.
        var sut = new RedisHashSetVectorStoreRecordCollection<SinglePropsModel>(
            this._redisDatabaseMock.Object,
            TestCollectionName,
            new() { VectorStoreRecordDefinition = definition, HashEntriesCustomMapper = Mock.Of<IVectorStoreRecordMapper<SinglePropsModel, (string key, HashEntry[] hashEntries)>>() });
    }

    private RedisHashSetVectorStoreRecordCollection<SinglePropsModel> CreateRecordCollection(bool useDefinition)
    {
        return new RedisHashSetVectorStoreRecordCollection<SinglePropsModel>(
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
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("OriginalNameData", typeof(string)),
            new VectorStoreRecordDataProperty("Data", typeof(string)) { StoragePropertyName = "data_storage_name" },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "vector_storage_name", DistanceFunction = DistanceFunction.CosineDistance }
        ]
    };

    public sealed class SinglePropsModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData(IsFilterable = true)]
        public string OriginalNameData { get; set; } = string.Empty;

        [JsonPropertyName("ignored_data_json_name")]
        [VectorStoreRecordData(IsFilterable = true, StoragePropertyName = "data_storage_name")]
        public string Data { get; set; } = string.Empty;

        [JsonPropertyName("ignored_vector_json_name")]
        [VectorStoreRecordVector(4, DistanceFunction.CosineDistance, StoragePropertyName = "vector_storage_name")]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }
}
