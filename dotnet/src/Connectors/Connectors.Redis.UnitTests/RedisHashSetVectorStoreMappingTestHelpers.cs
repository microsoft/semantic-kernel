// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using System.Runtime.InteropServices;
using Microsoft.Extensions.VectorData;
using StackExchange.Redis;
using Xunit;

namespace Microsoft.SemanticKernel.Connectors.Redis.UnitTests;

/// <summary>
/// Contains helper methods and data for testing the mapping of records between storage and data models.
/// These helpers are shared between the different mapping tests.
/// </summary>
internal static class RedisHashSetVectorStoreMappingTestHelpers
{
    public static readonly VectorStoreRecordDefinition s_vectorStoreRecordDefinition = new()
    {
        Properties = new List<VectorStoreRecordProperty>()
        {
            new VectorStoreRecordKeyProperty("Key", typeof(string)),
            new VectorStoreRecordDataProperty("StringData", typeof(string)) { StoragePropertyName = "storage_string_data" },
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
            new VectorStoreRecordVectorProperty("FloatVector", typeof(ReadOnlyMemory<float>), 10),
            new VectorStoreRecordVectorProperty("DoubleVector", typeof(ReadOnlyMemory<double>), 10),
        }
    };

    public static HashEntry[] CreateHashSet()
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

    public static void VerifyHashSet(HashEntry[] hashEntries)
    {
        Assert.Equal("storage_string_data", hashEntries[0].Name.ToString());
        Assert.Equal("data 1", hashEntries[0].Value.ToString());

        Assert.Equal("IntData", hashEntries[1].Name.ToString());
        Assert.Equal(1, (int)hashEntries[1].Value);

        Assert.Equal("UIntData", hashEntries[2].Name.ToString());
        Assert.Equal(2u, (uint)hashEntries[2].Value);

        Assert.Equal("LongData", hashEntries[3].Name.ToString());
        Assert.Equal(3, (long)hashEntries[3].Value);

        Assert.Equal("ULongData", hashEntries[4].Name.ToString());
        Assert.Equal(4ul, (ulong)hashEntries[4].Value);

        Assert.Equal("DoubleData", hashEntries[5].Name.ToString());
        Assert.Equal(5.5d, (double)hashEntries[5].Value);

        Assert.Equal("FloatData", hashEntries[6].Name.ToString());
        Assert.Equal(6.6f, (float)hashEntries[6].Value);

        Assert.Equal("BoolData", hashEntries[7].Name.ToString());
        Assert.True((bool)hashEntries[7].Value);

        Assert.Equal("NullableIntData", hashEntries[8].Name.ToString());
        Assert.Equal(7, (int)hashEntries[8].Value);

        Assert.Equal("NullableUIntData", hashEntries[9].Name.ToString());
        Assert.Equal(8u, (uint)hashEntries[9].Value);

        Assert.Equal("NullableLongData", hashEntries[10].Name.ToString());
        Assert.Equal(9, (long)hashEntries[10].Value);

        Assert.Equal("NullableULongData", hashEntries[11].Name.ToString());
        Assert.Equal(10ul, (ulong)hashEntries[11].Value);

        Assert.Equal("NullableDoubleData", hashEntries[12].Name.ToString());
        Assert.Equal(11.1d, (double)hashEntries[12].Value);

        Assert.Equal("NullableFloatData", hashEntries[13].Name.ToString());
        Assert.Equal(12.2f, (float)hashEntries[13].Value);

        Assert.Equal("NullableBoolData", hashEntries[14].Name.ToString());
        Assert.False((bool)hashEntries[14].Value);

        Assert.Equal("FloatVector", hashEntries[15].Name.ToString());
        Assert.Equal(new float[] { 1, 2, 3, 4 }, MemoryMarshal.Cast<byte, float>((byte[])hashEntries[15].Value!).ToArray());

        Assert.Equal("DoubleVector", hashEntries[16].Name.ToString());
        Assert.Equal(new double[] { 5, 6, 7, 8 }, MemoryMarshal.Cast<byte, double>((byte[])hashEntries[16].Value!).ToArray());
    }
}
