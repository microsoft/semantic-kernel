// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.SemanticKernel.Connectors.Redis;
using Microsoft.SemanticKernel.Data;
using StackExchange.Redis;
using Xunit;

namespace SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains tests for the <see cref="RedisHashSetVectorStoreRecordMapper{TConsumerDataModel}"/> class.
/// </summary>
public sealed class RedisHashSetVectorStoreRecordMapperTests
{
    [Fact]
    public void MapsAllFieldsFromDataToStorageModel()
    {
        // Arrange.
        var sut = new RedisHashSetVectorStoreRecordMapper<AllTypesModel>(s_vectorStoreRecordDefinition, s_storagePropertyNames);

        // Act.
        var actual = sut.MapFromDataToStorageModel(CreateModel("test key"));

        // Assert.
        Assert.NotNull(actual.HashEntries);
        Assert.Equal("test key", actual.Key);

        Assert.Equal("storage_string_data", actual.HashEntries[0].Name.ToString());
        Assert.Equal("data 1", actual.HashEntries[0].Value.ToString());

        Assert.Equal("IntData", actual.HashEntries[1].Name.ToString());
        Assert.Equal(1, (int)actual.HashEntries[1].Value);

        Assert.Equal("UIntData", actual.HashEntries[2].Name.ToString());
        Assert.Equal(2u, (uint)actual.HashEntries[2].Value);

        Assert.Equal("LongData", actual.HashEntries[3].Name.ToString());
        Assert.Equal(3, (long)actual.HashEntries[3].Value);

        Assert.Equal("ULongData", actual.HashEntries[4].Name.ToString());
        Assert.Equal(4ul, (ulong)actual.HashEntries[4].Value);

        Assert.Equal("DoubleData", actual.HashEntries[5].Name.ToString());
        Assert.Equal(5.5d, (double)actual.HashEntries[5].Value);

        Assert.Equal("FloatData", actual.HashEntries[6].Name.ToString());
        Assert.Equal(6.6f, (float)actual.HashEntries[6].Value);

        Assert.Equal("BoolData", actual.HashEntries[7].Name.ToString());
        Assert.True((bool)actual.HashEntries[7].Value);

        Assert.Equal("NullableIntData", actual.HashEntries[8].Name.ToString());
        Assert.Equal(7, (int)actual.HashEntries[8].Value);

        Assert.Equal("NullableUIntData", actual.HashEntries[9].Name.ToString());
        Assert.Equal(8u, (uint)actual.HashEntries[9].Value);

        Assert.Equal("NullableLongData", actual.HashEntries[10].Name.ToString());
        Assert.Equal(9, (long)actual.HashEntries[10].Value);

        Assert.Equal("NullableULongData", actual.HashEntries[11].Name.ToString());
        Assert.Equal(10ul, (ulong)actual.HashEntries[11].Value);

        Assert.Equal("NullableDoubleData", actual.HashEntries[12].Name.ToString());
        Assert.Equal(11.1d, (double)actual.HashEntries[12].Value);

        Assert.Equal("NullableFloatData", actual.HashEntries[13].Name.ToString());
        Assert.Equal(12.2f, (float)actual.HashEntries[13].Value);

        Assert.Equal("NullableBoolData", actual.HashEntries[14].Name.ToString());
        Assert.False((bool)actual.HashEntries[14].Value);

        Assert.Equal("FloatVector", actual.HashEntries[15].Name.ToString());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, MemoryMarshal.Cast<byte, float>((byte[])actual.HashEntries[15].Value!).ToArray());

        Assert.Equal("DoubleVector", actual.HashEntries[16].Name.ToString());
        Assert.Equal(new double[] { 5, 6, 7, 8 }, MemoryMarshal.Cast<byte, double>((byte[])actual.HashEntries[16].Value!).ToArray());
    }

    [Fact]
    public void MapsAllFieldsFromStorageToDataModel()
    {
        // Arrange.
        var sut = new RedisHashSetVectorStoreRecordMapper<AllTypesModel>(s_vectorStoreRecordDefinition, s_storagePropertyNames);

        // Act.
        var actual = sut.MapFromStorageToDataModel(("test key", CreateHashSet()), new() { IncludeVectors = true });

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

    private static HashEntry[] CreateHashSet()
    {
        var hashSet = new HashEntry[17];
        hashSet[0] = new HashEntry("storage_string_data", "data 1");
        hashSet[1] = new HashEntry("IntData", 1);
        hashSet[2] = new HashEntry("UIntData", 2);
        hashSet[3] = new HashEntry("LongData", 3);
        hashSet[4] = new HashEntry("ULongData", 4);
        hashSet[5] = new HashEntry("DoubleData", 5.5);
        hashSet[6] = new HashEntry("FloatData", 6.6);
        hashSet[7] = new HashEntry("BoolData", true);
        hashSet[8] = new HashEntry("NullableIntData", 7);
        hashSet[9] = new HashEntry("NullableUIntData", 8);
        hashSet[10] = new HashEntry("NullableLongData", 9);
        hashSet[11] = new HashEntry("NullableULongData", 10);
        hashSet[12] = new HashEntry("NullableDoubleData", 11.1);
        hashSet[13] = new HashEntry("NullableFloatData", 12.2);
        hashSet[14] = new HashEntry("NullableBoolData", false);
        hashSet[15] = new HashEntry("FloatVector", MemoryMarshal.AsBytes(new ReadOnlySpan<float>(new float[] { 1, 2, 3, 4 })).ToArray());
        hashSet[16] = new HashEntry("DoubleVector", MemoryMarshal.AsBytes(new ReadOnlySpan<double>(new double[] { 5, 6, 7, 8 })).ToArray());
        return hashSet;
    }

    private static readonly Dictionary<string, string> s_storagePropertyNames = new()
    {
        ["StringData"] = "storage_string_data",
        ["IntData"] = "IntData",
        ["UIntData"] = "UIntData",
        ["LongData"] = "LongData",
        ["ULongData"] = "ULongData",
        ["DoubleData"] = "DoubleData",
        ["FloatData"] = "FloatData",
        ["BoolData"] = "BoolData",
        ["NullableIntData"] = "NullableIntData",
        ["NullableUIntData"] = "NullableUIntData",
        ["NullableLongData"] = "NullableLongData",
        ["NullableULongData"] = "NullableULongData",
        ["NullableDoubleData"] = "NullableDoubleData",
        ["NullableFloatData"] = "NullableFloatData",
        ["NullableBoolData"] = "NullableBoolData",
        ["FloatVector"] = "FloatVector",
        ["DoubleVector"] = "DoubleVector",
    };

    private static readonly VectorStoreRecordDefinition s_vectorStoreRecordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>()
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringData", typeof(string)),
            new VectorStoreRecordDataProperty("IntData", typeof(int)),
            new VectorStoreRecordDataProperty("UIntData", typeof(uint)),
            new VectorStoreRecordDataProperty("LongData", typeof(long)),
            new VectorStoreRecordDataProperty("ULongData", typeof(ulong)),
            new VectorStoreRecordDataProperty("DoubleData", typeof(double)),
            new VectorStoreRecordDataProperty("FloatData", typeof(float)),
            new VectorStoreRecordDataProperty("BoolData", typeof(bool)),
            new VectorStoreRecordDataProperty("NullableIntData", typeof(int?)),
            new VectorStoreRecordDataProperty("NullableUIntData", typeof(uint?)),
            new VectorStoreRecordDataProperty("NullableLongData", typeof(long?)),
            new VectorStoreRecordDataProperty("NullableULongData", typeof(ulong?)),
            new VectorStoreRecordDataProperty("NullableDoubleData", typeof(double?)),
            new VectorStoreRecordDataProperty("NullableFloatData", typeof(float?)),
            new VectorStoreRecordDataProperty("NullableBoolData", typeof(bool?)),
            new VectorStoreRecordVectorProperty("FloatVector", typeof(float)),
            new VectorStoreRecordVectorProperty("DoubleVector", typeof(double)),
        }
    };

    private sealed class AllTypesModel
    {
        [VectorStoreRecordKey]
        public string Key { get; set; } = string.Empty;

        [VectorStoreRecordData]
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

        [VectorStoreRecordVector]
        public ReadOnlyMemory<float>? FloatVector { get; set; }

        [VectorStoreRecordVector]
        public ReadOnlyMemory<double>? DoubleVector { get; set; }

        public string NotAnnotated { get; set; } = string.Empty;
    }
}
