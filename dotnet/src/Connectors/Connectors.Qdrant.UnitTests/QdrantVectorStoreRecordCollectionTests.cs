// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.VectorData;
using Moq;
using Qdrant.Client.Grpc;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Qdrant.UnitTests;

/// <summary>
/// Contains tests for the <see cref="QdrantVectorStoreRecordCollection{TKey, TRecord}"/> class.
/// </summary>
public class QdrantVectorStoreRecordCollectionTests
{
    private const string TestCollectionName = "testcollection";
    private const ulong UlongTestRecordKey1 = 1;
    private const ulong UlongTestRecordKey2 = 2;
    private static readonly Guid s_guidTestRecordKey1 = Guid.Parse("11111111-1111-1111-1111-111111111111");
    private static readonly Guid s_guidTestRecordKey2 = Guid.Parse("22222222-2222-2222-2222-222222222222");

    private readonly Mock<MockableQdrantClient> _qdrantClientMock;

    private readonly CancellationToken _testCancellationToken = new(false);

    public QdrantVectorStoreRecordCollectionTests()
    {
        this._qdrantClientMock = new Mock<MockableQdrantClient>(MockBehavior.Strict);
    }

    [Theory]
    [InlineData(TestCollectionName, true)]
    [InlineData("nonexistentcollection", false)]
    public async Task CollectionExistsReturnsCollectionStateAsync(string collectionName, bool expectedExists)
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>(this._qdrantClientMock.Object, collectionName);

        this._qdrantClientMock
            .Setup(x => x.CollectionExistsAsync(
                It.IsAny<string>(),
                this._testCancellationToken))
            .ReturnsAsync(expectedExists);

        // Act.
        var actual = await sut.CollectionExistsAsync(this._testCancellationToken);

        // Assert.
        Assert.Equal(expectedExists, actual);
    }

    [Fact]
    public async Task CanCreateCollectionAsync()
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>(this._qdrantClientMock.Object, TestCollectionName);

        this._qdrantClientMock
            .Setup(x => x.CreateCollectionAsync(
                It.IsAny<string>(),
                It.IsAny<VectorParams>(),
                this._testCancellationToken))
            .Returns(Task.CompletedTask);

        this._qdrantClientMock
            .Setup(x => x.CreatePayloadIndexAsync(
                It.IsAny<string>(),
                It.IsAny<string>(),
                It.IsAny<PayloadSchemaType>(),
                this._testCancellationToken))
            .ReturnsAsync(new UpdateResult());

        // Act.
        await sut.CreateCollectionAsync(this._testCancellationToken);

        // Assert.
        this._qdrantClientMock
            .Verify(
                x => x.CreateCollectionAsync(
                    TestCollectionName,
                    It.Is<VectorParams>(x => x.Size == 4),
                    this._testCancellationToken),
                Times.Once);

        this._qdrantClientMock
            .Verify(
                x => x.CreatePayloadIndexAsync(
                    TestCollectionName,
                    "OriginalNameData",
                    PayloadSchemaType.Keyword,
                    this._testCancellationToken),
                Times.Once);

        this._qdrantClientMock
            .Verify(
                x => x.CreatePayloadIndexAsync(
                    TestCollectionName,
                    "OriginalNameData",
                    PayloadSchemaType.Text,
                    this._testCancellationToken),
                Times.Once);

        this._qdrantClientMock
            .Verify(
                x => x.CreatePayloadIndexAsync(
                    TestCollectionName,
                    "data_storage_name",
                    PayloadSchemaType.Keyword,
                    this._testCancellationToken),
                Times.Once);
    }

    [Fact]
    public async Task CanDeleteCollectionAsync()
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>(this._qdrantClientMock.Object, TestCollectionName);

        this._qdrantClientMock
            .Setup(x => x.DeleteCollectionAsync(
                It.IsAny<string>(),
                null,
                this._testCancellationToken))
            .Returns(Task.CompletedTask);

        // Act.
        await sut.DeleteCollectionAsync(this._testCancellationToken);

        // Assert.
        this._qdrantClientMock
            .Verify(
                x => x.DeleteCollectionAsync(
                    TestCollectionName,
                    null,
                    this._testCancellationToken),
                Times.Once);
    }

    [Theory]
    [MemberData(nameof(TestOptions))]
    public async Task CanGetRecordWithVectorsAsync<TKey>(bool useDefinition, bool hasNamedVectors, TKey testRecordKey)
        where TKey : notnull
    {
        var sut = this.CreateRecordCollection<TKey>(useDefinition, hasNamedVectors);

        // Arrange.
        var retrievedPoint = CreateRetrievedPoint(hasNamedVectors, testRecordKey);
        this.SetupRetrieveMock([retrievedPoint]);

        // Act.
        var actual = await sut.GetAsync(
            testRecordKey,
            new() { IncludeVectors = true },
            this._testCancellationToken);

        // Assert.
        this._qdrantClientMock
            .Verify(
                x => x.RetrieveAsync(
                    TestCollectionName,
                    It.Is<IReadOnlyList<PointId>>(x => x.Count == 1 && (testRecordKey!.GetType() == typeof(ulong) && x[0].Num == (testRecordKey as ulong?) || testRecordKey!.GetType() == typeof(Guid) && x[0].Uuid == (testRecordKey as Guid?).ToString())),
                    true,
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);

        Assert.NotNull(actual);
        Assert.Equal(testRecordKey, actual.Key);
        Assert.Equal("data 1", actual.OriginalNameData);
        Assert.Equal("data 1", actual.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
    }

    [Theory]
    [MemberData(nameof(TestOptions))]
    public async Task CanGetRecordWithoutVectorsAsync<TKey>(bool useDefinition, bool hasNamedVectors, TKey testRecordKey)
        where TKey : notnull
    {
        // Arrange.
        var sut = this.CreateRecordCollection<TKey>(useDefinition, hasNamedVectors);
        var retrievedPoint = CreateRetrievedPoint(hasNamedVectors, testRecordKey);
        this.SetupRetrieveMock([retrievedPoint]);

        // Act.
        var actual = await sut.GetAsync(
            testRecordKey,
            new() { IncludeVectors = false },
            this._testCancellationToken);

        // Assert.
        this._qdrantClientMock
            .Verify(
                x => x.RetrieveAsync(
                    TestCollectionName,
                    It.Is<IReadOnlyList<PointId>>(x => x.Count == 1 && (testRecordKey!.GetType() == typeof(ulong) && x[0].Num == (testRecordKey as ulong?) || testRecordKey!.GetType() == typeof(Guid) && x[0].Uuid == (testRecordKey as Guid?).ToString())),
                    true,
                    false,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);

        Assert.NotNull(actual);
        Assert.Equal(testRecordKey, actual.Key);
        Assert.Equal("data 1", actual.OriginalNameData);
        Assert.Equal("data 1", actual.Data);
        Assert.Null(actual.Vector);
    }

    [Theory]
    [MemberData(nameof(MultiRecordTestOptions))]
    public async Task CanGetManyRecordsWithVectorsAsync<TKey>(bool useDefinition, bool hasNamedVectors, TKey[] testRecordKeys)
        where TKey : notnull
    {
        // Arrange.
        var sut = this.CreateRecordCollection<TKey>(useDefinition, hasNamedVectors);
        var retrievedPoint1 = CreateRetrievedPoint(hasNamedVectors, UlongTestRecordKey1);
        var retrievedPoint2 = CreateRetrievedPoint(hasNamedVectors, UlongTestRecordKey2);
        this.SetupRetrieveMock(testRecordKeys.Select(x => CreateRetrievedPoint(hasNamedVectors, x)).ToList());

        // Act.
        var actual = await sut.GetAsync(
            testRecordKeys,
            new() { IncludeVectors = true },
            this._testCancellationToken).ToListAsync();

        // Assert.
        this._qdrantClientMock
            .Verify(
                x => x.RetrieveAsync(
                    TestCollectionName,
                    It.Is<IReadOnlyList<PointId>>(x =>
                        x.Count == 2 &&
                        (testRecordKeys[0]!.GetType() == typeof(ulong) && x[0].Num == (testRecordKeys[0] as ulong?) || testRecordKeys[0]!.GetType() == typeof(Guid) && x[0].Uuid == (testRecordKeys[0] as Guid?).ToString()) &&
                        (testRecordKeys[1]!.GetType() == typeof(ulong) && x[1].Num == (testRecordKeys[1] as ulong?) || testRecordKeys[1]!.GetType() == typeof(Guid) && x[1].Uuid == (testRecordKeys[1] as Guid?).ToString())),
                    true,
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);

        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(testRecordKeys[0], actual[0].Key);
        Assert.Equal(testRecordKeys[1], actual[1].Key);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanDeleteUlongRecordAsync(bool useDefinition, bool hasNamedVectors)
    {
        // Arrange
        var sut = this.CreateRecordCollection<ulong>(useDefinition, hasNamedVectors);
        this.SetupDeleteMocks();

        // Act
        await sut.DeleteAsync(
            UlongTestRecordKey1,
            cancellationToken: this._testCancellationToken);

        // Assert
        this._qdrantClientMock
            .Verify(
                x => x.DeleteAsync(
                    TestCollectionName,
                    It.Is<ulong>(x => x == UlongTestRecordKey1),
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanDeleteGuidRecordAsync(bool useDefinition, bool hasNamedVectors)
    {
        // Arrange
        var sut = this.CreateRecordCollection<Guid>(useDefinition, hasNamedVectors);
        this.SetupDeleteMocks();

        // Act
        await sut.DeleteAsync(
            s_guidTestRecordKey1,
            cancellationToken: this._testCancellationToken);

        // Assert
        this._qdrantClientMock
            .Verify(
                x => x.DeleteAsync(
                    TestCollectionName,
                    It.Is<Guid>(x => x == s_guidTestRecordKey1),
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanDeleteManyUlongRecordsAsync(bool useDefinition, bool hasNamedVectors)
    {
        // Arrange
        var sut = this.CreateRecordCollection<ulong>(useDefinition, hasNamedVectors);
        this.SetupDeleteMocks();

        // Act
        await sut.DeleteAsync(
            [UlongTestRecordKey1, UlongTestRecordKey2],
            cancellationToken: this._testCancellationToken);

        // Assert
        this._qdrantClientMock
            .Verify(
                x => x.DeleteAsync(
                    TestCollectionName,
                    It.Is<IReadOnlyList<ulong>>(x => x.Count == 2 && x.Contains(UlongTestRecordKey1) && x.Contains(UlongTestRecordKey2)),
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public async Task CanDeleteManyGuidRecordsAsync(bool useDefinition, bool hasNamedVectors)
    {
        // Arrange
        var sut = this.CreateRecordCollection<Guid>(useDefinition, hasNamedVectors);
        this.SetupDeleteMocks();

        // Act
        await sut.DeleteAsync(
            [s_guidTestRecordKey1, s_guidTestRecordKey2],
            cancellationToken: this._testCancellationToken);

        // Assert
        this._qdrantClientMock
            .Verify(
                x => x.DeleteAsync(
                    TestCollectionName,
                    It.Is<IReadOnlyList<Guid>>(x => x.Count == 2 && x.Contains(s_guidTestRecordKey1) && x.Contains(s_guidTestRecordKey2)),
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);
    }

    [Theory]
    [MemberData(nameof(TestOptions))]
    public async Task CanUpsertRecordAsync<TKey>(bool useDefinition, bool hasNamedVectors, TKey testRecordKey)
        where TKey : notnull
    {
        // Arrange
        var sut = this.CreateRecordCollection<TKey>(useDefinition, hasNamedVectors);
        this.SetupUpsertMock();

        // Act
        await sut.UpsertAsync(
            CreateModel(testRecordKey, true),
            cancellationToken: this._testCancellationToken);

        // Assert
        this._qdrantClientMock
            .Verify(
                x => x.UpsertAsync(
                    TestCollectionName,
                    It.Is<IReadOnlyList<PointStruct>>(x => x.Count == 1 && (testRecordKey!.GetType() == typeof(ulong) && x[0].Id.Num == (testRecordKey as ulong?) || testRecordKey!.GetType() == typeof(Guid) && x[0].Id.Uuid == (testRecordKey as Guid?).ToString())),
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);
    }

    [Theory]
    [MemberData(nameof(MultiRecordTestOptions))]
    public async Task CanUpsertManyRecordsAsync<TKey>(bool useDefinition, bool hasNamedVectors, TKey[] testRecordKeys)
        where TKey : notnull
    {
        // Arrange
        var sut = this.CreateRecordCollection<TKey>(useDefinition, hasNamedVectors);
        this.SetupUpsertMock();

        var models = testRecordKeys.Select(x => CreateModel(x, true));

        // Act
        var actual = await sut.UpsertAsync(
            models,
            cancellationToken: this._testCancellationToken);

        // Assert
        Assert.NotNull(actual);
        Assert.Equal(2, actual.Count);
        Assert.Equal(testRecordKeys[0], actual[0]);
        Assert.Equal(testRecordKeys[1], actual[1]);

        this._qdrantClientMock
            .Verify(
                x => x.UpsertAsync(
                    TestCollectionName,
                    It.Is<IReadOnlyList<PointStruct>>(x =>
                        x.Count == 2 &&
                        (testRecordKeys[0]!.GetType() == typeof(ulong) && x[0].Id.Num == (testRecordKeys[0] as ulong?) || testRecordKeys[0]!.GetType() == typeof(Guid) && x[0].Id.Uuid == (testRecordKeys[0] as Guid?).ToString()) &&
                        (testRecordKeys[1]!.GetType() == typeof(ulong) && x[1].Id.Num == (testRecordKeys[1] as ulong?) || testRecordKeys[1]!.GetType() == typeof(Guid) && x[1].Id.Uuid == (testRecordKeys[1] as Guid?).ToString())),
                    true,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);
    }

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
                new VectorStoreRecordKeyProperty(nameof(SinglePropsModel<ulong>.Key), typeof(ulong)),
                new VectorStoreRecordDataProperty(nameof(SinglePropsModel<ulong>.OriginalNameData), typeof(string)),
                new VectorStoreRecordVectorProperty(nameof(SinglePropsModel<ulong>.Vector), typeof(ReadOnlyMemory<float>?), 4),
            }
        };

        // Act.
        var sut = new QdrantVectorStoreRecordCollection<ulong, SinglePropsModel<ulong>>(
            this._qdrantClientMock.Object,
            TestCollectionName,
            new() { VectorStoreRecordDefinition = definition });
    }

#pragma warning disable CS0618 // VectorSearchFilter is obsolete
    [Theory]
    [MemberData(nameof(TestOptions))]
    public async Task CanSearchWithVectorAndFilterAsync<TKey>(bool useDefinition, bool hasNamedVectors, TKey testRecordKey)
        where TKey : notnull
    {
        var sut = this.CreateRecordCollection<TKey>(useDefinition, hasNamedVectors);

        // Arrange.
        var scoredPoint = CreateScoredPoint(hasNamedVectors, testRecordKey);
        this.SetupQueryMock([scoredPoint]);
        var filter = new VectorSearchFilter().EqualTo(nameof(SinglePropsModel<TKey>.Data), "data 1");

        // Act.
        var results = await sut.VectorizedSearchAsync(
            new ReadOnlyMemory<float>(new[] { 1f, 2f, 3f, 4f }),
            top: 5,
            new() { IncludeVectors = true, OldFilter = filter, Skip = 2 },
            this._testCancellationToken).ToListAsync();

        // Assert.
        this._qdrantClientMock
            .Verify(
                x => x.QueryAsync(
                    TestCollectionName,
                    It.Is<Query?>(x => x!.Nearest.Dense.Data.ToArray().SequenceEqual(new[] { 1f, 2f, 3f, 4f })),
                    null,
                    hasNamedVectors ? "vector_storage_name" : null,
                    It.Is<Filter?>(x => x!.Must.Count == 1 && x.Must.First().Field.Key == "data_storage_name" && x.Must.First().Field.Match.Keyword == "data 1"),
                    null,
                    null,
                    5,
                    2,
                    null,
                    It.Is<WithVectorsSelector?>(x => x!.Enable == true),
                    null,
                    null,
                    null,
                    null,
                    this._testCancellationToken),
                Times.Once);

        Assert.Single(results);
        Assert.Equal(testRecordKey, results.First().Record.Key);
        Assert.Equal("data 1", results.First().Record.OriginalNameData);
        Assert.Equal("data 1", results.First().Record.Data);
        Assert.Equal(new float[] { 1, 2, 3, 4 }, results.First().Record.Vector!.Value.ToArray());
        Assert.Equal(0.5f, results.First().Score);
    }
#pragma warning restore CS0618 // VectorSearchFilter is obsolete

    private void SetupRetrieveMock(List<RetrievedPoint> retrievedPoints)
    {
        this._qdrantClientMock
            .Setup(x => x.RetrieveAsync(
                It.IsAny<string>(),
                It.IsAny<IReadOnlyList<PointId>>(),
                It.IsAny<bool>(), // With Payload
                It.IsAny<bool>(), // With Vectors
                It.IsAny<ReadConsistency>(),
                It.IsAny<ShardKeySelector>(),
                this._testCancellationToken))
            .ReturnsAsync(retrievedPoints);
    }

    private void SetupQueryMock(List<ScoredPoint> scoredPoints)
    {
        this._qdrantClientMock
            .Setup(x => x.QueryAsync(
                It.IsAny<string>(),
                It.IsAny<Query?>(),
                null,
                It.IsAny<string?>(),
                It.IsAny<Filter?>(),
                null,
                null,
                It.IsAny<ulong>(),
                It.IsAny<ulong>(),
                null,
                It.IsAny<WithVectorsSelector?>(),
                null,
                null,
                null,
                null,
                It.IsAny<CancellationToken>()))
            .ReturnsAsync(scoredPoints);
    }

    private void SetupDeleteMocks()
    {
        this._qdrantClientMock
            .Setup(x => x.DeleteAsync(
                It.IsAny<string>(),
                It.IsAny<ulong>(),
                It.IsAny<bool>(), // wait
                It.IsAny<WriteOrderingType?>(),
                It.IsAny<ShardKeySelector?>(),
                this._testCancellationToken))
            .ReturnsAsync(new UpdateResult());

        this._qdrantClientMock
            .Setup(x => x.DeleteAsync(
                It.IsAny<string>(),
                It.IsAny<Guid>(),
                It.IsAny<bool>(), // wait
                It.IsAny<WriteOrderingType?>(),
                It.IsAny<ShardKeySelector?>(),
                this._testCancellationToken))
            .ReturnsAsync(new UpdateResult());

        this._qdrantClientMock
            .Setup(x => x.DeleteAsync(
                It.IsAny<string>(),
                It.IsAny<IReadOnlyList<ulong>>(),
                It.IsAny<bool>(), // wait
                It.IsAny<WriteOrderingType?>(),
                It.IsAny<ShardKeySelector?>(),
                this._testCancellationToken))
            .ReturnsAsync(new UpdateResult());

        this._qdrantClientMock
            .Setup(x => x.DeleteAsync(
                It.IsAny<string>(),
                It.IsAny<IReadOnlyList<Guid>>(),
                It.IsAny<bool>(), // wait
                It.IsAny<WriteOrderingType?>(),
                It.IsAny<ShardKeySelector?>(),
                this._testCancellationToken))
            .ReturnsAsync(new UpdateResult());
    }

    private void SetupUpsertMock()
    {
        this._qdrantClientMock
            .Setup(x => x.UpsertAsync(
                It.IsAny<string>(),
                It.IsAny<IReadOnlyList<PointStruct>>(),
                It.IsAny<bool>(), // wait
                It.IsAny<WriteOrderingType?>(),
                It.IsAny<ShardKeySelector?>(),
                this._testCancellationToken))
            .ReturnsAsync(new UpdateResult());
    }

    private static RetrievedPoint CreateRetrievedPoint<TKey>(bool hasNamedVectors, TKey recordKey)
    {
        var responseVector = VectorOutput.Parser.ParseJson("{ \"data\": [1, 2, 3, 4] }");

        RetrievedPoint point;
        if (hasNamedVectors)
        {
            var namedVectors = new NamedVectorsOutput();
            namedVectors.Vectors.Add("vector_storage_name", responseVector);
            point = new RetrievedPoint()
            {
                Payload = { ["OriginalNameData"] = "data 1", ["data_storage_name"] = "data 1" },
                Vectors = new VectorsOutput { Vectors = namedVectors }
            };
        }
        else
        {
            point = new RetrievedPoint()
            {
                Payload = { ["OriginalNameData"] = "data 1", ["data_storage_name"] = "data 1" },
                Vectors = new VectorsOutput() { Vector = responseVector }
            };
        }

        if (recordKey is ulong ulongKey)
        {
            point.Id = ulongKey;
        }

        if (recordKey is Guid guidKey)
        {
            point.Id = guidKey;
        }

        return point;
    }

    private static ScoredPoint CreateScoredPoint<TKey>(bool hasNamedVectors, TKey recordKey)
    {
        var responseVector = VectorOutput.Parser.ParseJson("{ \"data\": [1, 2, 3, 4] }");

        ScoredPoint point;
        if (hasNamedVectors)
        {
            var namedVectors = new NamedVectorsOutput();
            namedVectors.Vectors.Add("vector_storage_name", responseVector);
            point = new ScoredPoint()
            {
                Score = 0.5f,
                Payload = { ["OriginalNameData"] = "data 1", ["data_storage_name"] = "data 1" },
                Vectors = new VectorsOutput { Vectors = namedVectors }
            };
        }
        else
        {
            point = new ScoredPoint()
            {
                Score = 0.5f,
                Payload = { ["OriginalNameData"] = "data 1", ["data_storage_name"] = "data 1" },
                Vectors = new VectorsOutput() { Vector = responseVector }
            };
        }

        if (recordKey is ulong ulongKey)
        {
            point.Id = ulongKey;
        }

        if (recordKey is Guid guidKey)
        {
            point.Id = guidKey;
        }

        return point;
    }

    private IVectorStoreRecordCollection<T, SinglePropsModel<T>> CreateRecordCollection<T>(bool useDefinition, bool hasNamedVectors)
        where T : notnull
    {
        var store = new QdrantVectorStoreRecordCollection<T, SinglePropsModel<T>>(
            this._qdrantClientMock.Object,
            TestCollectionName,
            new()
            {
                VectorStoreRecordDefinition = useDefinition ? CreateSinglePropsDefinition(typeof(T)) : null,
                HasNamedVectors = hasNamedVectors
            }) as IVectorStoreRecordCollection<T, SinglePropsModel<T>>;
        return store!;
    }

    private static SinglePropsModel<T> CreateModel<T>(T key, bool withVectors)
    {
        return new SinglePropsModel<T>
        {
            Key = key,
            OriginalNameData = "data 1",
            Data = "data 1",
            Vector = withVectors ? new float[] { 1, 2, 3, 4 } : null,
            NotAnnotated = null,
        };
    }

    private static VectorStoreRecordDefinition CreateSinglePropsDefinition(Type keyType)
    {
        return new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty("Key", keyType),
                new VectorStoreRecordDataProperty("OriginalNameData", typeof(string)) { IsIndexed = true, IsFullTextIndexed = true },
                new VectorStoreRecordDataProperty("Data", typeof(string)) { IsIndexed = true, StoragePropertyName = "data_storage_name" },
                new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 4) { StoragePropertyName = "vector_storage_name" }
            ]
        };
    }

    public sealed class SinglePropsModel<T>
    {
        [VectorStoreRecordKey]
        public required T Key { get; set; }

        [VectorStoreRecordData(IsIndexed = true, IsFullTextIndexed = true)]
        public string OriginalNameData { get; set; } = string.Empty;

        [JsonPropertyName("ignored_data_json_name")]
        [VectorStoreRecordData(IsIndexed = true, StoragePropertyName = "data_storage_name")]
        public string Data { get; set; } = string.Empty;

        [JsonPropertyName("ignored_vector_json_name")]
        [VectorStoreRecordVector(4, StoragePropertyName = "vector_storage_name")]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string? NotAnnotated { get; set; }
    }

    public static IEnumerable<object[]> TestOptions
        => GenerateAllCombinations(new object[][] {
                new object[] { true, false },
                new object[] { true, false },
                new object[] { UlongTestRecordKey1, s_guidTestRecordKey1 }
        });

    public static IEnumerable<object[]> MultiRecordTestOptions
    => GenerateAllCombinations(new object[][] {
                new object[] { true, false },
                new object[] { true, false },
                new object[] { new ulong[] { UlongTestRecordKey1, UlongTestRecordKey2 }, new Guid[] { s_guidTestRecordKey1, s_guidTestRecordKey2 } }
    });

    private static object[][] GenerateAllCombinations(object[][] input)
    {
        var counterArray = Enumerable.Range(0, input.Length).Select(x => 0).ToArray();

        // Add each item from the first option set as a separate row.
        object[][] currentCombinations = input[0].Select(x => new object[1] { x }).ToArray();

        // Loop through each additional option set.
        for (int currentOptionSetIndex = 1; currentOptionSetIndex < input.Length; currentOptionSetIndex++)
        {
            var iterationCombinations = new List<object[]>();
            var currentOptionSet = input[currentOptionSetIndex];

            // Loop through each row we have already.
            foreach (var currentCombination in currentCombinations)
            {
                // Add each of the values from the new options set to the current row to generate a new row.
                for (var currentColumnRow = 0; currentColumnRow < currentOptionSet.Length; currentColumnRow++)
                {
                    iterationCombinations.Add(currentCombination.Append(currentOptionSet[currentColumnRow]).ToArray());
                }
            }

            currentCombinations = iterationCombinations.ToArray();
        }

        return currentCombinations;
    }
}
