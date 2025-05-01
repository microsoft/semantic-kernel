// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ConnectorSupport;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Connectors.Redis.UnitTests;
using Xunit;

namespace SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisHashSetVectorStoreRecordMapper{TConsumerDataModel}"/> class.
/// </summary>
public sealed class RedisHashSetVectorStoreRecordMapperTests
{
    private static readonly VectorStoreRecordModel s_model
        = new VectorStoreRecordModelBuilder(RedisHashSetVectorStoreRecordCollection<string, AllTypesModel>.ModelBuildingOptions)
            .Build(typeof(AllTypesModel), RedisHashSetVectorStoreMappingTestHelpers.s_vectorStoreRecordDefinition, defaultEmbeddingGenerator: null);

    [Fact]
    public void MapsAllFieldsFromDataToStorageModel()
    {
        // Arrange.
        var sut = new RedisHashSetVectorStoreRecordMapper<AllTypesModel>(s_model);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateModel("test key"), recordIndex: 0, generatedEmbeddings: null);

        // Assert.
        Assert.NotNull(actual.HashEntries);
        Assert.Equal("test key", actual.Key);
        RedisHashSetVectorStoreMappingTestHelpers.VerifyHashSet(actual.HashEntries);
    }

    [Fact]
    public void MapsAllFieldsFromStorageToDataModel()
    {
        // Arrange.
        var sut = new RedisHashSetVectorStoreRecordMapper<AllTypesModel>(s_model);

        // Act.
        var actual = sut.MapFromStorageToDataModel(("test key", RedisHashSetVectorStoreMappingTestHelpers.CreateHashSet()), new() { IncludeVectors = true });

        // Assert.
        Assert.NotNull(actual);
        Assert.Equal("test key", actual.Key);
        Assert.Equal("data 1", actual.StringData);
        Assert.Equal(1, actual.IntData);
        Assert.Equal(2u, actual.UIntData);
        Assert.Equal(3, actual.LongData);
        Assert.Equal(4ul, actual.ULongData);
        Assert.Equal(5.5d, actual.DoubleData);
        Assert.Equal(6.6f, actual.FloatData);
        Assert.True(actual.BoolData);
        Assert.Equal(7, actual.NullableIntData);
        Assert.Equal(8u, actual.NullableUIntData);
        Assert.Equal(9, actual.NullableLongData);
        Assert.Equal(10ul, actual.NullableULongData);
        Assert.Equal(11.1d, actual.NullableDoubleData);
        Assert.Equal(12.2f, actual.NullableFloatData);
        Assert.False(actual.NullableBoolData);

        Assert.Equal(new float[] { 1, 2, 3, 4 }, actual.FloatVector!.Value.ToArray());
        Assert.Equal(new double[] { 5, 6, 7, 8 }, actual.DoubleVector!.Value.ToArray());
    }

    private static AllTypesModel CreateModel(string key)
    {
        return new AllTypesModel
        {
            Key = key,
            StringData = "data 1",
            IntData = 1,
            UIntData = 2,
            LongData = 3,
            ULongData = 4,
            DoubleData = 5.5d,
            FloatData = 6.6f,
            BoolData = true,
            NullableIntData = 7,
            NullableUIntData = 8,
            NullableLongData = 9,
            NullableULongData = 10,
            NullableDoubleData = 11.1d,
            NullableFloatData = 12.2f,
            NullableBoolData = false,
            FloatVector = new float[] { 1, 2, 3, 4 },
            DoubleVector = new double[] { 5, 6, 7, 8 },
            NotAnnotated = "notAnnotated",
        };
    }

    private sealed class AllTypesModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData(StoragePropertyName = "storage_string_data")]
        public string StringData { get; set; } = string.Empty;

        [VectorStoreRecordData]
        public int IntData { get; set; }

        [VectorStoreRecordData]
        public uint UIntData { get; set; }

        [VectorStoreRecordData]
        public long LongData { get; set; }

        [VectorStoreRecordData]
        public ulong ULongData { get; set; }

        [VectorStoreRecordData]
        public double DoubleData { get; set; }

        [VectorStoreRecordData]
        public float FloatData { get; set; }

        [VectorStoreRecordData]
        public bool BoolData { get; set; }

        [VectorStoreRecordData]
        public int? NullableIntData { get; set; }

        [VectorStoreRecordData]
        public uint? NullableUIntData { get; set; }

        [VectorStoreRecordData]
        public long? NullableLongData { get; set; }

        [VectorStoreRecordData]
        public ulong? NullableULongData { get; set; }

        [VectorStoreRecordData]
        public double? NullableDoubleData { get; set; }

        [VectorStoreRecordData]
        public float? NullableFloatData { get; set; }

        [VectorStoreRecordData]
        public bool? NullableBoolData { get; set; }

        [VectorStoreRecordVector(10)]
        public ReadOnlyMemory<float>? FloatVector { get; set; }

        [VectorStoreRecordVector(10)]
        public ReadOnlyMemory<double>? DoubleVector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
