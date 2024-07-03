// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using Microsoft.SemanticKernel.Connectors.Qdrant;
using Microsoft.SemanticKernel.Data;
using Qdrant.Client.Grpc;
using Xunit;

namespace SemanticKernel.Connectors.Qdrant.UnitTests;

/// <summary>
/// Contains tests for the <see cref="QdrantVectorStoreRecordMapper{TConsumerDataModel}"/> class.
/// </summary>
public class QdrantVectorStoreRecordMapperTests
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapsSinglePropsFromDataToStorageModelWithUlong(bool hasNamedVectors)
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<ulong>>(new() { HasNamedVectors = hasNamedVectors });

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateSinglePropsModel<ulong>(5ul));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(5ul, actual.Id.Num);
        Assert.Single(actual.Payload);
        Assert.Equal("data", actual.Payload["Data"].StringValue);

        if (hasNamedVectors)
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vectors.Vectors_.Vectors["Vector"].Data.ToArray());
        }
        else
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vectors.Vector.Data.ToArray());
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapsSinglePropsFromDataToStorageModelWithGuid(bool hasNamedVectors)
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<Guid>>(new() { HasNamedVectors = hasNamedVectors });

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateSinglePropsModel<Guid>(Guid.Parse("11111111-1111-1111-1111-111111111111")));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), Guid.Parse(actual.Id.Uuid));
        Assert.Single(actual.Payload);
        Assert.Equal("data", actual.Payload["Data"].StringValue);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public void MapsSinglePropsFromStorageToDataModelWithUlong(bool hasNamedVectors, bool includeVectors)
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<ulong>>(new() { HasNamedVectors = hasNamedVectors });

        // Act.
        var actual = sut.MapFromStorageToDataModel(CreateSinglePropsPointStruct(5, hasNamedVectors), new() { IncludeVectors = includeVectors });

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(5ul, actual.Key);
        Assert.Equal("data", actual.Data);

        if (includeVectors)
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
        }
        else
        {
            Assert.Null(actual.Vector);
        }
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public void MapsSinglePropsFromStorageToDataModelWithGuid(bool hasNamedVectors, bool includeVectors)
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<Guid>>(new() { HasNamedVectors = hasNamedVectors });

        // Act.
        var actual = sut.MapFromStorageToDataModel(CreateSinglePropsPointStruct(Guid.Parse("11111111-1111-1111-1111-111111111111"), hasNamedVectors), new() { IncludeVectors = includeVectors });

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), actual.Key);
        Assert.Equal("data", actual.Data);

        if (includeVectors)
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector!.Value.ToArray());
        }
        else
        {
            Assert.Null(actual.Vector);
        }
    }

    [Fact]
    public void MapsMultiPropsFromDataToStorageModelWithUlong()
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<ulong>>(new() { HasNamedVectors = true });

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateMultiPropsModel<ulong>(5ul));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(5ul, actual.Id.Num);
        Assert.Equal(7, actual.Payload.Count);
        Assert.Equal("data 1", actual.Payload["DataString"].StringValue);
        Assert.Equal(5, actual.Payload["DataInt"].IntegerValue);
        Assert.Equal(5, actual.Payload["DataLong"].IntegerValue);
        Assert.Equal(5.5f, actual.Payload["DataFloat"].DoubleValue);
        Assert.Equal(5.5d, actual.Payload["DataDouble"].DoubleValue);
        Assert.True(actual.Payload["DataBool"].BoolValue);
        Assert.Equal(new int[] { 1, 2, 3, 4 }, actual.Payload["DataArrayInt"].ListValue.Values.Select(x => (int)x.IntegerValue).ToArray());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vectors.Vectors_.Vectors["Vector1"].Data.ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vectors.Vectors_.Vectors["Vector2"].Data.ToArray());
    }

    [Fact]
    public void MapsMultiPropsFromDataToStorageModelWithGuid()
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<Guid>>(new() { HasNamedVectors = true });

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateMultiPropsModel<Guid>(Guid.Parse("11111111-1111-1111-1111-111111111111")));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), Guid.Parse(actual.Id.Uuid));
        Assert.Equal(7, actual.Payload.Count);
        Assert.Equal("data 1", actual.Payload["DataString"].StringValue);
        Assert.Equal(5, actual.Payload["DataInt"].IntegerValue);
        Assert.Equal(5, actual.Payload["DataLong"].IntegerValue);
        Assert.Equal(5.5f, actual.Payload["DataFloat"].DoubleValue);
        Assert.Equal(5.5d, actual.Payload["DataDouble"].DoubleValue);
        Assert.True(actual.Payload["DataBool"].BoolValue);
        Assert.Equal(new int[] { 1, 2, 3, 4 }, actual.Payload["DataArrayInt"].ListValue.Values.Select(x => (int)x.IntegerValue).ToArray());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vectors.Vectors_.Vectors["Vector1"].Data.ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vectors.Vectors_.Vectors["Vector2"].Data.ToArray());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapsMultiPropsFromStorageToDataModelWithUlong(bool includeVectors)
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<ulong>>(new() { HasNamedVectors = true });

        // Act.
        var actual = sut.MapFromStorageToDataModel(CreateMultiPropsPointStruct(5), new() { IncludeVectors = includeVectors });

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(5ul, actual.Key);
        Assert.Equal("data 1", actual.DataString);
        Assert.Equal(5, actual.DataInt);
        Assert.Equal(5L, actual.DataLong);
        Assert.Equal(5.5f, actual.DataFloat);
        Assert.Equal(5.5d, actual.DataDouble);
        Assert.True(actual.DataBool);
        Assert.Equal(new int[] { 1, 2, 3, 4 }, actual.DataArrayInt);

        if (includeVectors)
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector1!.Value.ToArray());
            Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vector2!.Value.ToArray());
        }
        else
        {
            Assert.Null(actual.Vector1);
            Assert.Null(actual.Vector2);
        }
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapsMultiPropsFromStorageToDataModelWithGuid(bool includeVectors)
    {
        // Arrange.
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<Guid>>(new() { HasNamedVectors = true });

        // Act.
        var actual = sut.MapFromStorageToDataModel(CreateMultiPropsPointStruct(Guid.Parse("11111111-1111-1111-1111-111111111111")), new() { IncludeVectors = includeVectors });

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), actual.Key);
        Assert.Equal("data 1", actual.DataString);
        Assert.Equal(5, actual.DataInt);
        Assert.Equal(5L, actual.DataLong);
        Assert.Equal(5.5f, actual.DataFloat);
        Assert.Equal(5.5d, actual.DataDouble);
        Assert.True(actual.DataBool);
        Assert.Equal(new int[] { 1, 2, 3, 4 }, actual.DataArrayInt);

        if (includeVectors)
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vector1!.Value.ToArray());
            Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vector2!.Value.ToArray());
        }
        else
        {
            Assert.Null(actual.Vector1);
            Assert.Null(actual.Vector2);
        }
    }

    private static SinglePropsModel<TKey> CreateSinglePropsModel<TKey>(TKey key)
    {
        return new SinglePropsModel<TKey>
        {
            Key = key,
            Data = "data",
            Vector = new float[] { 1, 2, 3, 4 },
            NotAnnotated = "notAnnotated",
        };
    }

    private static MultiPropsModel<TKey> CreateMultiPropsModel<TKey>(TKey key)
    {
        return new MultiPropsModel<TKey>
        {
            Key = key,
            DataString = "data 1",
            DataInt = 5,
            DataLong = 5L,
            DataFloat = 5.5f,
            DataDouble = 5.5d,
            DataBool = true,
            DataArrayInt = new List<int> { 1, 2, 3, 4 },
            Vector1 = new float[] { 1, 2, 3, 4 },
            Vector2 = new float[] { 5, 6, 7, 8 },
            NotAnnotated = "notAnnotated",
        };
    }

    private static PointStruct CreateSinglePropsPointStruct(ulong id, bool hasNamedVectors)
    {
        var pointStruct = new PointStruct();
        pointStruct.Id = new PointId() { Num = id };
        AddDataToSinglePropsPointStruct(pointStruct, hasNamedVectors);
        return pointStruct;
    }

    private static PointStruct CreateSinglePropsPointStruct(Guid id, bool hasNamedVectors)
    {
        var pointStruct = new PointStruct();
        pointStruct.Id = new PointId() { Uuid = id.ToString() };
        AddDataToSinglePropsPointStruct(pointStruct, hasNamedVectors);
        return pointStruct;
    }

    private static void AddDataToSinglePropsPointStruct(PointStruct pointStruct, bool hasNamedVectors)
    {
        pointStruct.Payload.Add("Data", "data");

        if (hasNamedVectors)
        {
            var namedVectors = new NamedVectors();
            namedVectors.Vectors.Add("Vector", new[] { 1f, 2f, 3f, 4f });
            pointStruct.Vectors = new Vectors() { Vectors_ = namedVectors };
        }
        else
        {
            pointStruct.Vectors = new[] { 1f, 2f, 3f, 4f };
        }
    }

    private static PointStruct CreateMultiPropsPointStruct(ulong id)
    {
        var pointStruct = new PointStruct();
        pointStruct.Id = new PointId() { Num = id };
        AddDataToMultiPropsPointStruct(pointStruct);
        return pointStruct;
    }

    private static PointStruct CreateMultiPropsPointStruct(Guid id)
    {
        var pointStruct = new PointStruct();
        pointStruct.Id = new PointId() { Uuid = id.ToString() };
        AddDataToMultiPropsPointStruct(pointStruct);
        return pointStruct;
    }

    private static void AddDataToMultiPropsPointStruct(PointStruct pointStruct)
    {
        pointStruct.Payload.Add("DataString", "data 1");
        pointStruct.Payload.Add("DataInt", 5);
        pointStruct.Payload.Add("DataLong", 5L);
        pointStruct.Payload.Add("DataFloat", 5.5f);
        pointStruct.Payload.Add("DataDouble", 5.5d);
        pointStruct.Payload.Add("DataBool", true);

        var dataIntArray = new ListValue();
        dataIntArray.Values.Add(1);
        dataIntArray.Values.Add(2);
        dataIntArray.Values.Add(3);
        dataIntArray.Values.Add(4);
        pointStruct.Payload.Add("DataArrayInt", new Value { ListValue = dataIntArray });

        var namedVectors = new NamedVectors();
        namedVectors.Vectors.Add("Vector1", new[] { 1f, 2f, 3f, 4f });
        namedVectors.Vectors.Add("Vector2", new[] { 5f, 6f, 7f, 8f });
        pointStruct.Vectors = new Vectors() { Vectors_ = namedVectors };
    }

    private sealed class SinglePropsModel<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; } = default;

        [VectorStoreRecordData]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private sealed class MultiPropsModel<TKey>
    {
        [VectorStoreRecordKey]
        public TKey? Key { get; set; } = default;

        [VectorStoreRecordData(HasEmbedding = true, EmbeddingPropertyName = "Vector1")]
        public string DataString { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public int DataInt { get; set; } = 0;

        [VectorStoreRecordData]
        public long DataLong { get; set; } = 0;

        [VectorStoreRecordData]
        public float DataFloat { get; set; } = 0;

        [VectorStoreRecordData]
        public double DataDouble { get; set; } = 0;

        [VectorStoreRecordData]
        public bool DataBool { get; set; } = false;

        [VectorStoreRecordData]
        public List<int>? DataArrayInt { get; set; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector1 { get; set; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
