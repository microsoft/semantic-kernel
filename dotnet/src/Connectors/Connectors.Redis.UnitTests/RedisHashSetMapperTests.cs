// Copyright (c) Microsoft. All rights reserved.

using System;
using Microsoft.Extensions.VectorData;
using Microsoft.Extensions.VectorData.ProviderServices;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Connectors.Redis.UnitTests;
using Xunit;

namespace SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisHashSetMapper{TConsumerDataModel}"/> class.
/// </summary>
public sealed class RedisHashSetMapperTests
{
    private static readonly CollectionModel s_model
        = new RedisModelBuilder(RedisHashSetCollection<string, AllTypesModel>.ModelBuildingOptions)
            .Build(typeof(AllTypesModel), RedisHashSetMappingTestHelpers.s_definition, defaultEmbeddingGenerator: null);

    [Fact]
    public void MapsAllFieldsFromDataToStorageModel()
    {
        // Arrange.
        var sut = new RedisHashSetMapper<AllTypesModel>(s_model);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateModel("test key"), recordIndex: 0, generatedEmbeddings: null);

        // Assert.
        Assert.NotNull(actual.HashEntries);
        Assert.Equal("test key", actual.Key);
        RedisHashSetMappingTestHelpers.VerifyHashSet(actual.HashEntries);
    }

    [Fact]
    public void MapsAllFieldsFromStorageToDataModel()
    {
        // Arrange.
        var sut = new RedisHashSetMapper<AllTypesModel>(s_model);

        // Act.
        var actual = sut.MapFromStorageToDataModel(("test key", RedisHashSetMappingTestHelpers.CreateHashSet()), includeVectors: true);

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
        [VectorStoreKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreData(StorageName = "storage_string_data")]
        public string StringData { get; set; } = string.Empty;

        [VectorStoreData]
        public int IntData { get; set; }

        [VectorStoreData]
        public uint UIntData { get; set; }

        [VectorStoreData]
        public long LongData { get; set; }

        [VectorStoreData]
        public ulong ULongData { get; set; }

        [VectorStoreData]
        public double DoubleData { get; set; }

        [VectorStoreData]
        public float FloatData { get; set; }

        [VectorStoreData]
        public bool BoolData { get; set; }

        [VectorStoreData]
        public int? NullableIntData { get; set; }

        [VectorStoreData]
        public uint? NullableUIntData { get; set; }

        [VectorStoreData]
        public long? NullableLongData { get; set; }

        [VectorStoreData]
        public ulong? NullableULongData { get; set; }

        [VectorStoreData]
        public double? NullableDoubleData { get; set; }

        [VectorStoreData]
        public float? NullableFloatData { get; set; }

        [VectorStoreData]
        public bool? NullableBoolData { get; set; }

        [VectorStoreVector(10)]
        public ReadOnlyMemory<float>? FloatVector { get; set; }

        [VectorStoreVector(10)]
        public ReadOnlyMemory<double>? DoubleVector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
