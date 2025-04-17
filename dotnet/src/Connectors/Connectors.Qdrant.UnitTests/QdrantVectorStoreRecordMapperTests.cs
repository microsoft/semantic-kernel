// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Linq;
using System.Text.Json.Serialization;
using Microsoft.Extensions.VectorData;
using Microsoft.SemanticKernel.Connectors.Qdrant;
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
        var definition = CreateSinglePropsVectorStoreRecordDefinition(typeof(ulong));
        var reader = new VectorStoreRecordPropertyReader(typeof(SinglePropsModel<ulong>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<ulong>>(reader, hasNamedVectors);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateSinglePropsModel<ulong>(5ul));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(5ul, actual.Id.Num);
        Assert.Single(actual.Payload);
        Assert.Equal("data value", actual.Payload["data"].StringValue);

        if (hasNamedVectors)
        {
            Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vectors.Vectors_.Vectors["vector"].Data.ToArray());
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
        var definition = CreateSinglePropsVectorStoreRecordDefinition(typeof(Guid));
        var reader = new VectorStoreRecordPropertyReader(typeof(SinglePropsModel<Guid>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<Guid>>(reader, hasNamedVectors);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateSinglePropsModel<Guid>(Guid.Parse("11111111-1111-1111-1111-111111111111")));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), Guid.Parse(actual.Id.Uuid));
        Assert.Single(actual.Payload);
        Assert.Equal("data value", actual.Payload["data"].StringValue);
    }

    [Theory]
    [InlineData(true, true)]
    [InlineData(true, false)]
    [InlineData(false, true)]
    [InlineData(false, false)]
    public void MapsSinglePropsFromStorageToDataModelWithUlong(bool hasNamedVectors, bool includeVectors)
    {
        // Arrange.
        var definition = CreateSinglePropsVectorStoreRecordDefinition(typeof(ulong));
        var reader = new VectorStoreRecordPropertyReader(typeof(SinglePropsModel<ulong>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<ulong>>(reader, hasNamedVectors);

        // Act.
        var actual = sut.MapFromStorageToDataModel(CreateSinglePropsPointStruct(5, hasNamedVectors), new() { IncludeVectors = includeVectors });

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(5ul, actual.Key);
        Assert.Equal("data value", actual.Data);

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
        var definition = CreateSinglePropsVectorStoreRecordDefinition(typeof(Guid));
        var reader = new VectorStoreRecordPropertyReader(typeof(SinglePropsModel<Guid>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<SinglePropsModel<Guid>>(reader, hasNamedVectors);

        // Act.
        var actual = sut.MapFromStorageToDataModel(CreateSinglePropsPointStruct(Guid.Parse("11111111-1111-1111-1111-111111111111"), hasNamedVectors), new() { IncludeVectors = includeVectors });

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), actual.Key);
        Assert.Equal("data value", actual.Data);

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
        var definition = CreateMultiPropsVectorStoreRecordDefinition(typeof(ulong));
        var reader = new VectorStoreRecordPropertyReader(typeof(MultiPropsModel<ulong>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<ulong>>(reader, true);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateMultiPropsModel<ulong>(5ul));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(5ul, actual.Id.Num);
        Assert.Equal(8, actual.Payload.Count);
        Assert.Equal("data 1", actual.Payload["dataString"].StringValue);
        Assert.Equal(5, actual.Payload["dataInt"].IntegerValue);
        Assert.Equal(5, actual.Payload["dataLong"].IntegerValue);
        Assert.Equal(5.5f, actual.Payload["dataFloat"].DoubleValue);
        Assert.Equal(5.5d, actual.Payload["dataDouble"].DoubleValue);
        Assert.True(actual.Payload["dataBool"].BoolValue);
        Assert.Equal("2025-02-10T05:10:15.0000000+01:00", actual.Payload["dataDateTimeOffset"].StringValue);
        Assert.Equal(new int[] { 1, 2, 3, 4 }, actual.Payload["dataArrayInt"].ListValue.Values.Select(x => (int)x.IntegerValue).ToArray());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vectors.Vectors_.Vectors["vector1"].Data.ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vectors.Vectors_.Vectors["vector2"].Data.ToArray());
    }

    [Fact]
    public void MapsMultiPropsFromDataToStorageModelWithGuid()
    {
        // Arrange.
        var definition = CreateMultiPropsVectorStoreRecordDefinition(typeof(Guid));
        var reader = new VectorStoreRecordPropertyReader(typeof(MultiPropsModel<Guid>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<Guid>>(reader, true);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateMultiPropsModel<Guid>(Guid.Parse("11111111-1111-1111-1111-111111111111")));

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal(Guid.Parse("11111111-1111-1111-1111-111111111111"), Guid.Parse(actual.Id.Uuid));
        Assert.Equal(8, actual.Payload.Count);
        Assert.Equal("data 1", actual.Payload["dataString"].StringValue);
        Assert.Equal(5, actual.Payload["dataInt"].IntegerValue);
        Assert.Equal(5, actual.Payload["dataLong"].IntegerValue);
        Assert.Equal(5.5f, actual.Payload["dataFloat"].DoubleValue);
        Assert.Equal(5.5d, actual.Payload["dataDouble"].DoubleValue);
        Assert.True(actual.Payload["dataBool"].BoolValue);
        Assert.Equal("2025-02-10T05:10:15.0000000+01:00", actual.Payload["dataDateTimeOffset"].StringValue);
        Assert.Equal(new int[] { 1, 2, 3, 4 }, actual.Payload["dataArrayInt"].ListValue.Values.Select(x => (int)x.IntegerValue).ToArray());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.Vectors.Vectors_.Vectors["vector1"].Data.ToArray());
        Assert.Equal(new float[] { 5, 6, 7, 8 }, actual.Vectors.Vectors_.Vectors["vector2"].Data.ToArray());
    }

    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapsMultiPropsFromStorageToDataModelWithUlong(bool includeVectors)
    {
        // Arrange.
        var definition = CreateMultiPropsVectorStoreRecordDefinition(typeof(ulong));
        var reader = new VectorStoreRecordPropertyReader(typeof(MultiPropsModel<ulong>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<ulong>>(reader, true);

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
        Assert.Equal(new DateTimeOffset(2025, 2, 10, 5, 10, 15, TimeSpan.FromHours(1)), actual.DataDateTimeOffset);
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
        var definition = CreateMultiPropsVectorStoreRecordDefinition(typeof(Guid));
        var reader = new VectorStoreRecordPropertyReader(typeof(MultiPropsModel<Guid>), definition, null);
        var sut = new QdrantVectorStoreRecordMapper<MultiPropsModel<Guid>>(reader, true);

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
        Assert.Equal(new DateTimeOffset(2025, 2, 10, 5, 10, 15, TimeSpan.FromHours(1)), actual.DataDateTimeOffset);
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
            Data = "data value",
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
            DataDateTimeOffset = new DateTimeOffset(2025, 2, 10, 5, 10, 15, TimeSpan.FromHours(1)),
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
        pointStruct.Payload.Add("data", "data value");

        if (hasNamedVectors)
        {
            var namedVectors = new NamedVectors();
            namedVectors.Vectors.Add("vector", new[] { 1f, 2f, 3f, 4f });
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
        pointStruct.Payload.Add("dataString", "data 1");
        pointStruct.Payload.Add("dataInt", 5);
        pointStruct.Payload.Add("dataLong", 5L);
        pointStruct.Payload.Add("dataFloat", 5.5f);
        pointStruct.Payload.Add("dataDouble", 5.5d);
        pointStruct.Payload.Add("dataBool", true);
        pointStruct.Payload.Add("dataDateTimeOffset", "2025-02-10T05:10:15.0000000+01:00");

        var dataIntArray = new ListValue();
        dataIntArray.Values.Add(1);
        dataIntArray.Values.Add(2);
        dataIntArray.Values.Add(3);
        dataIntArray.Values.Add(4);
        pointStruct.Payload.Add("dataArrayInt", new Value { ListValue = dataIntArray });

        var namedVectors = new NamedVectors();
        namedVectors.Vectors.Add("vector1", new[] { 1f, 2f, 3f, 4f });
        namedVectors.Vectors.Add("vector2", new[] { 5f, 6f, 7f, 8f });
        pointStruct.Vectors = new Vectors() { Vectors_ = namedVectors };
    }

    private static VectorStoreRecordDefinition CreateSinglePropsVectorStoreRecordDefinition(Type keyType) => new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", keyType) { StoragePropertyName = "key" },
            new VectorStoreRecordDataProperty("Data", typeof(string)) { StoragePropertyName = "data" },
            new VectorStoreRecordVectorProperty("Vector", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "vector" },
        },
    };

    private sealed class SinglePropsModel<TKey>
    {
        [VectorStoreRecordKey(StoragePropertyName = "key")]
        public TKey? Key { get; set; } = default;

        [VectorStoreRecordData(StoragePropertyName = "data")]
        public string Data { get; set; } = string.Empty;

        [VectorStoreRecordVector(StoragePropertyName = "vector")]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private static VectorStoreRecordDefinition CreateMultiPropsVectorStoreRecordDefinition(Type keyType) => new()
    {
        Properties = new List<VectorStoreRecordProperty>
        {
            new VectorStoreRecordKeyProperty("Key", keyType) { StoragePropertyName = "key" },
            new VectorStoreRecordDataProperty("DataString", typeof(string)) { StoragePropertyName = "dataString" },
            new VectorStoreRecordDataProperty("DataInt", typeof(int)) { StoragePropertyName = "dataInt" },
            new VectorStoreRecordDataProperty("DataLong", typeof(long)) { StoragePropertyName = "dataLong" },
            new VectorStoreRecordDataProperty("DataFloat", typeof(float)) { StoragePropertyName = "dataFloat" },
            new VectorStoreRecordDataProperty("DataDouble", typeof(double)) { StoragePropertyName = "dataDouble" },
            new VectorStoreRecordDataProperty("DataBool", typeof(bool)) { StoragePropertyName = "dataBool" },
            new VectorStoreRecordDataProperty("DataDateTimeOffset", typeof(DateTimeOffset)) { StoragePropertyName = "dataDateTimeOffset" },
            new VectorStoreRecordDataProperty("DataArrayInt", typeof(List<int>)) { StoragePropertyName = "dataArrayInt" },
            new VectorStoreRecordVectorProperty("Vector1", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "vector1" },
            new VectorStoreRecordVectorProperty("Vector2", typeof(ReadOnlyMemory<float>)) { StoragePropertyName = "vector2" },
        },
    };

    private sealed class MultiPropsModel<TKey>
    {
        [VectorStoreRecordKey(StoragePropertyName = "key")]
        public TKey? Key { get; set; } = default;

        [VectorStoreRecordData(StoragePropertyName = "dataString")]
        public string DataString { get; set; } = string.Empty;

        [JsonPropertyName("data_int_json")]
        [VectorStoreRecordData(StoragePropertyName = "dataInt")]
        public int DataInt { get; set; } = 0;

        [VectorStoreRecordData(StoragePropertyName = "dataLong")]
        public long DataLong { get; set; } = 0;

        [VectorStoreRecordData(StoragePropertyName = "dataFloat")]
        public float DataFloat { get; set; } = 0;

        [VectorStoreRecordData(StoragePropertyName = "dataDouble")]
        public double DataDouble { get; set; } = 0;

        [VectorStoreRecordData(StoragePropertyName = "dataBool")]
        public bool DataBool { get; set; } = false;

        [VectorStoreRecordData(StoragePropertyName = "dataDateTimeOffset")]
        public DateTimeOffset DataDateTimeOffset { get; set; }

        [VectorStoreRecordData(StoragePropertyName = "dataArrayInt")]
        public List<int>? DataArrayInt { get; set; }

        [VectorStoreRecordVector(StoragePropertyName = "vector1")]
        public ReadOnlyMemory<float>? Vector1 { get; set; }

        [VectorStoreRecordVector(StoragePropertyName = "vector2")]
        public ReadOnlyMemory<float>? Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
