// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Xunit;

namespace AzureAISearch.ConformanceTests.Support;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
#pragma warning disable CA1819 // Properties should not return arrays

public class AzureAISearchAllTypes
{
    [VectorStoreKey]
    public string Id { get; set; }

    [VectorStoreData]
    public bool BoolProperty { get; set; }
    [VectorStoreData]
    public bool? NullableBoolProperty { get; set; }
    [VectorStoreData]
    public string StringProperty { get; set; }
    [VectorStoreData]
    public string? NullableStringProperty { get; set; }
    [VectorStoreData]
    public int IntProperty { get; set; }
    [VectorStoreData]
    public int? NullableIntProperty { get; set; }
    [VectorStoreData]
    public long LongProperty { get; set; }
    [VectorStoreData]
    public long? NullableLongProperty { get; set; }
    [VectorStoreData]
    public float FloatProperty { get; set; }
    [VectorStoreData]
    public float? NullableFloatProperty { get; set; }
    [VectorStoreData]
    public double DoubleProperty { get; set; }
    [VectorStoreData]
    public double? NullableDoubleProperty { get; set; }
    [VectorStoreData]
    public DateTimeOffset DateTimeOffsetProperty { get; set; }
    [VectorStoreData]
    public DateTimeOffset? NullableDateTimeOffsetProperty { get; set; }

    [VectorStoreData]
    public string[] StringArray { get; set; }
    [VectorStoreData]
    public List<string> StringList { get; set; }
    [VectorStoreData]
    public bool[] BoolArray { get; set; }
    [VectorStoreData]
    public List<bool> BoolList { get; set; }
    [VectorStoreData]
    public int[] IntArray { get; set; }
    [VectorStoreData]
    public List<int> IntList { get; set; }
    [VectorStoreData]
    public long[] LongArray { get; set; }
    [VectorStoreData]
    public List<long> LongList { get; set; }
    [VectorStoreData]
    public float[] FloatArray { get; set; }
    [VectorStoreData]
    public List<float> FloatList { get; set; }
    [VectorStoreData]
    public double[] DoubleArray { get; set; }
    [VectorStoreData]
    public List<double> DoubleList { get; set; }
    [VectorStoreData]
    public DateTimeOffset[] DateTimeOffsetArray { get; set; }
    [VectorStoreData]
    public List<DateTimeOffset> DateTimeOffsetList { get; set; }

    [VectorStoreVector(Dimensions: 8, DistanceFunction = DistanceFunction.DotProductSimilarity)]
    public ReadOnlyMemory<float>? Embedding { get; set; }

    internal void AssertEqual(AzureAISearchAllTypes other)
    {
        Assert.Equal(this.Id, other.Id);
        Assert.Equal(this.BoolProperty, other.BoolProperty);
        Assert.Equal(this.NullableBoolProperty, other.NullableBoolProperty);
        Assert.Equal(this.StringProperty, other.StringProperty);
        Assert.Equal(this.NullableStringProperty, other.NullableStringProperty);
        Assert.Equal(this.IntProperty, other.IntProperty);
        Assert.Equal(this.NullableIntProperty, other.NullableIntProperty);
        Assert.Equal(this.LongProperty, other.LongProperty);
        Assert.Equal(this.NullableLongProperty, other.NullableLongProperty);
        Assert.Equal(this.FloatProperty, other.FloatProperty);
        Assert.Equal(this.NullableFloatProperty, other.NullableFloatProperty);
        Assert.Equal(this.DoubleProperty, other.DoubleProperty);
        Assert.Equal(this.NullableDoubleProperty, other.NullableDoubleProperty);
        AssertEqual(this.DateTimeOffsetProperty, other.DateTimeOffsetProperty);
        Assert.Equal(this.NullableDateTimeOffsetProperty.HasValue, other.NullableDateTimeOffsetProperty.HasValue);
        if (this.NullableDateTimeOffsetProperty.HasValue && other.NullableDateTimeOffsetProperty.HasValue)
        {
            AssertEqual(this.NullableDateTimeOffsetProperty.Value, other.NullableDateTimeOffsetProperty.Value);
        }

        Assert.Equal(this.StringArray, other.StringArray);
        Assert.Equal(this.StringList, other.StringList);
        Assert.Equal(this.BoolArray, other.BoolArray);
        Assert.Equal(this.BoolList, other.BoolList);
        Assert.Equal(this.IntArray, other.IntArray);
        Assert.Equal(this.IntList, other.IntList);
        Assert.Equal(this.LongArray, other.LongArray);
        Assert.Equal(this.LongList, other.LongList);
        Assert.Equal(this.FloatArray, other.FloatArray);
        Assert.Equal(this.FloatList, other.FloatList);
        Assert.Equal(this.DoubleArray, other.DoubleArray);
        Assert.Equal(this.DoubleList, other.DoubleList);
        Assert.Equal(this.DateTimeOffsetArray.Length, other.DateTimeOffsetArray.Length);
        for (int i = 0; i < this.DateTimeOffsetArray.Length; i++)
        {
            AssertEqual(this.DateTimeOffsetArray[i], other.DateTimeOffsetArray[i]);
        }
        Assert.Equal(this.DateTimeOffsetList.Count, other.DateTimeOffsetList.Count);
        for (int i = 0; i < this.DateTimeOffsetList.Count; i++)
        {
            AssertEqual(this.DateTimeOffsetList[i], other.DateTimeOffsetList[i]);
        }

        Assert.Equal(this.Embedding!.Value.ToArray(), other.Embedding!.Value.ToArray());

        static void AssertEqual(DateTimeOffset expected, DateTimeOffset actual)
        {
            Assert.Equal(expected, actual, TimeSpan.FromSeconds(0.01));
        }
    }

    internal static VectorStoreCollectionDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreKeyProperty(nameof(AzureAISearchAllTypes.Id), typeof(string)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.BoolProperty), typeof(bool)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.NullableBoolProperty), typeof(bool?)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.StringProperty), typeof(string)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.NullableStringProperty), typeof(string)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.IntProperty), typeof(int)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.NullableIntProperty), typeof(int?)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.LongProperty), typeof(long)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.NullableLongProperty), typeof(long?)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.FloatProperty), typeof(float)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.NullableFloatProperty), typeof(float?)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.DoubleProperty), typeof(double)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.NullableDoubleProperty), typeof(double?)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.DateTimeOffsetProperty), typeof(DateTimeOffset)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.NullableDateTimeOffsetProperty), typeof(DateTimeOffset?)),

                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.StringArray), typeof(string[])),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.StringList), typeof(List<string>)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.BoolArray), typeof(bool[])),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.BoolList), typeof(List<bool>)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.IntArray), typeof(int[])),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.IntList), typeof(List<int>)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.LongArray), typeof(long[])),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.LongList), typeof(List<long>)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.FloatArray), typeof(float[])),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.FloatList), typeof(List<float>)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.DoubleArray), typeof(double[])),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.DoubleList), typeof(List<double>)),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.DateTimeOffsetArray), typeof(DateTimeOffset[])),
                new VectorStoreDataProperty(nameof(AzureAISearchAllTypes.DateTimeOffsetList), typeof(List<DateTimeOffset>)),

                new VectorStoreVectorProperty(nameof(AzureAISearchAllTypes.Embedding), typeof(ReadOnlyMemory<float>?), 8) { DistanceFunction = Microsoft.Extensions.VectorData.DistanceFunction.DotProductSimilarity }
            ]
        };
}
