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
/// Contains tests for the <see cref="QdrantMapper{TConsumerDataModel}"/> class.
/// </summary>
public class QdrantMapperTests
{
    [Theory]
    [InlineData(true)]
    [InlineData(false)]
    public void MapsSinglePropsFromDataToStorageModelWithUlong(bool hasNamedVectors)
    {
        // Arrange.
        var definition = CreateSinglePropsVectorStoreRecordDefinition(typeof(ulong));
        var model = new QdrantModelBuilder(hasNamedVectors)
            .Build(typeof(SinglePropsModel<ulong>), definition, defaultEmbeddingGenerator: null);
        var sut = new QdrantMapper<SinglePropsModel<ulong>>(model, hasNamedVectors);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateSinglePropsModel<ulong>(5ul), recordIndex: 0, generatedEmbeddings: null);

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
        var model = new QdrantModelBuilder(hasNamedVectors)
            .Build(typeof(SinglePropsModel<Guid>), definition, defaultEmbeddingGenerator: null);
        var sut = new QdrantMapper<SinglePropsModel<Guid>>(model, hasNamedVectors);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateSinglePropsModel<Guid>(Guid.Parse("11111111-1111-1111-1111-111111111111")), recordIndex: 0, generatedEmbeddings: null);

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
        var model = new QdrantModelBuilder(hasNamedVectors)
            .Build(typeof(SinglePropsModel<ulong>), definition, defaultEmbeddingGenerator: null);
        var sut = new QdrantMapper<SinglePropsModel<ulong>>(model, hasNamedVectors);

        // Act.
        var point = CreateSinglePropsPointStruct(5, hasNamedVectors);
        var actual = sut.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, includeVectors);

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
        var model = new QdrantModelBuilder(hasNamedVectors)
            .Build(typeof(SinglePropsModel<Guid>), definition, defaultEmbeddingGenerator: null);
        var sut = new QdrantMapper<SinglePropsModel<Guid>>(model, hasNamedVectors);

        // Act.
        var point = CreateSinglePropsPointStruct(Guid.Parse("11111111-1111-1111-1111-111111111111"), hasNamedVectors);
        var actual = sut.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, includeVectors);

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
        var model = new QdrantModelBuilder(hasNamedVectors: true)
            .Build(typeof(MultiPropsModel<ulong>), definition, defaultEmbeddingGenerator: null);

        var sut = new QdrantMapper<MultiPropsModel<ulong>>(model, hasNamedVectors: true);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateMultiPropsModel<ulong>(5ul), recordIndex: 0, generatedEmbeddings: null);

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
        var model = new QdrantModelBuilder(hasNamedVectors: true)
            .Build(typeof(MultiPropsModel<Guid>), definition, defaultEmbeddingGenerator: null);
        var sut = new QdrantMapper<MultiPropsModel<Guid>>(model, hasNamedVectors: true);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateMultiPropsModel<Guid>(Guid.Parse("11111111-1111-1111-1111-111111111111")), recordIndex: 0, generatedEmbeddings: null);

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
        var model = new QdrantModelBuilder(hasNamedVectors: true)
            .Build(typeof(MultiPropsModel<ulong>), definition, defaultEmbeddingGenerator: null);
        var sut = new QdrantMapper<MultiPropsModel<ulong>>(model, hasNamedVectors: true);

        // Act.
        var point = CreateMultiPropsPointStruct(5);
        var actual = sut.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, includeVectors);

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
        var model = new QdrantModelBuilder(hasNamedVectors: true)
            .Build(typeof(MultiPropsModel<Guid>), definition, defaultEmbeddingGenerator: null);
        var sut = new QdrantMapper<MultiPropsModel<Guid>>(model, hasNamedVectors: true);

        // Act.
        var point = CreateMultiPropsPointStruct(Guid.Parse("11111111-1111-1111-1111-111111111111"));
        var actual = sut.MapFromStorageToDataModel(point.Id, point.Payload, point.Vectors, includeVectors);

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

    private static RetrievedPoint CreateSinglePropsPointStruct(ulong id, bool hasNamedVectors)
    {
        var pointStruct = new RetrievedPoint();
        pointStruct.Id = new PointId() { Num = id };
        AddDataToSinglePropsPointStruct(pointStruct, hasNamedVectors);
        return pointStruct;
    }

    private static RetrievedPoint CreateSinglePropsPointStruct(Guid id, bool hasNamedVectors)
    {
        var pointStruct = new RetrievedPoint();
        pointStruct.Id = new PointId() { Uuid = id.ToString() };
        AddDataToSinglePropsPointStruct(pointStruct, hasNamedVectors);
        return pointStruct;
    }

    private static void AddDataToSinglePropsPointStruct(RetrievedPoint pointStruct, bool hasNamedVectors)
    {
        var responseVector = VectorOutput.Parser.ParseJson("{ \"data\": [1, 2, 3, 4] }");

        pointStruct.Payload.Add("data", "data value");

        if (hasNamedVectors)
        {
            var namedVectors = new NamedVectorsOutput();
            namedVectors.Vectors.Add("vector", responseVector);
            pointStruct.Vectors = new VectorsOutput() { Vectors = namedVectors };
        }
        else
        {
            pointStruct.Vectors = new VectorsOutput() { Vector = responseVector };
        }
    }

    private static RetrievedPoint CreateMultiPropsPointStruct(ulong id)
    {
        var pointStruct = new RetrievedPoint();
        pointStruct.Id = new PointId() { Num = id };
        AddDataToMultiPropsPointStruct(pointStruct);
        return pointStruct;
    }

    private static RetrievedPoint CreateMultiPropsPointStruct(Guid id)
    {
        var pointStruct = new RetrievedPoint();
        pointStruct.Id = new PointId() { Uuid = id.ToString() };
        AddDataToMultiPropsPointStruct(pointStruct);
        return pointStruct;
    }

    private static void AddDataToMultiPropsPointStruct(RetrievedPoint pointStruct)
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

        var responseVector1 = VectorOutput.Parser.ParseJson("{ \"data\": [1, 2, 3, 4] }");
        var responseVector2 = VectorOutput.Parser.ParseJson("{ \"data\": [5, 6, 7, 8] }");

        var namedVectors = new NamedVectorsOutput();
        namedVectors.Vectors.Add("vector1", responseVector1);
        namedVectors.Vectors.Add("vector2", responseVector2);
        pointStruct.Vectors = new VectorsOutput() { Vectors = namedVectors };
    }

    private static VectorStoreCollectionDefinition CreateSinglePropsVectorStoreRecordDefinition(Type keyType) => new()
    {
        Properties = new List<VectorStoreProperty>
        {
            new VectorStoreKeyProperty("Key", keyType) { StorageName = "key" },
            new VectorStoreDataProperty("Data", typeof(string)) { StorageName = "data" },
            new VectorStoreVectorProperty("Vector", typeof(ReadOnlyMemory<float>), 10) { StorageName = "vector" },
        },
    };

    private sealed class SinglePropsModel<TKey>
    {
        [VectorStoreKey(StorageName = "key")]
        public TKey? Key { get; set; } = default;

        [VectorStoreData(StorageName = "data")]
        public string Data { get; set; } = string.Empty;

        [VectorStoreVector(10, StorageName = "vector")]
        public ReadOnlyMemory<float>? Vector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }

    private static VectorStoreCollectionDefinition CreateMultiPropsVectorStoreRecordDefinition(Type keyType) => new()
    {
        Properties = new List<VectorStoreProperty>
        {
            new VectorStoreKeyProperty("Key", keyType) { StorageName = "key" },
            new VectorStoreDataProperty("DataString", typeof(string)) { StorageName = "dataString" },
            new VectorStoreDataProperty("DataInt", typeof(int)) { StorageName = "dataInt" },
            new VectorStoreDataProperty("DataLong", typeof(long)) { StorageName = "dataLong" },
            new VectorStoreDataProperty("DataFloat", typeof(float)) { StorageName = "dataFloat" },
            new VectorStoreDataProperty("DataDouble", typeof(double)) { StorageName = "dataDouble" },
            new VectorStoreDataProperty("DataBool", typeof(bool)) { StorageName = "dataBool" },
            new VectorStoreDataProperty("DataDateTimeOffset", typeof(DateTimeOffset)) { StorageName = "dataDateTimeOffset" },
            new VectorStoreDataProperty("DataArrayInt", typeof(List<int>)) { StorageName = "dataArrayInt" },
            new VectorStoreVectorProperty("Vector1", typeof(ReadOnlyMemory<float>), 10) { StorageName = "vector1" },
            new VectorStoreVectorProperty("Vector2", typeof(ReadOnlyMemory<float>), 10) { StorageName = "vector2" },
        },
    };

    private sealed class MultiPropsModel<TKey>
    {
        [VectorStoreKey(StorageName = "key")]
        public TKey? Key { get; set; } = default;

        [VectorStoreData(StorageName = "dataString")]
        public string DataString { get; set; } = string.Empty;

        [JsonPropertyName("data_int_json")]
        [VectorStoreData(StorageName = "dataInt")]
        public int DataInt { get; set; } = 0;

        [VectorStoreData(StorageName = "dataLong")]
        public long DataLong { get; set; } = 0;

        [VectorStoreData(StorageName = "dataFloat")]
        public float DataFloat { get; set; } = 0;

        [VectorStoreData(StorageName = "dataDouble")]
        public double DataDouble { get; set; } = 0;

        [VectorStoreData(StorageName = "dataBool")]
        public bool DataBool { get; set; } = false;

        [VectorStoreData(StorageName = "dataDateTimeOffset")]
        public DateTimeOffset DataDateTimeOffset { get; set; }

        [VectorStoreData(StorageName = "dataArrayInt")]
        public List<int>? DataArrayInt { get; set; }

        [VectorStoreVector(10, StorageName = "vector1")]
        public ReadOnlyMemory<float>? Vector1 { get; set; }

        [VectorStoreVector(10, StorageName = "vector2")]
        public ReadOnlyMemory<float>? Vector2 { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
