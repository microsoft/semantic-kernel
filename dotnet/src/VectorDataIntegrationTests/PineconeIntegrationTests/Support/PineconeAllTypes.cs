// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Xunit;

namespace PineconeIntegrationTests.Support;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
public record PineconeAllTypes()
{
    [VectorStoreRecordKey]
    public string Id { get; set; }

    [VectorStoreRecordData]
    public bool BoolProperty { get; set; }
    [VectorStoreRecordData]
    public bool? NullableBoolProperty { get; set; }
    [VectorStoreRecordData]
    public string StringProperty { get; set; }
    [VectorStoreRecordData]
    public string? NullableStringProperty { get; set; }
    [VectorStoreRecordData]
    public int IntProperty { get; set; }
    [VectorStoreRecordData]
    public int? NullableIntProperty { get; set; }
    [VectorStoreRecordData]
    public long LongProperty { get; set; }
    [VectorStoreRecordData]
    public long? NullableLongProperty { get; set; }
    [VectorStoreRecordData]
    public float FloatProperty { get; set; }
    [VectorStoreRecordData]
    public float? NullableFloatProperty { get; set; }
    [VectorStoreRecordData]
    public double DoubleProperty { get; set; }
    [VectorStoreRecordData]
    public double? NullableDoubleProperty { get; set; }

#pragma warning disable CA1819 // Properties should not return arrays
    [VectorStoreRecordData]
    public string[] StringArray { get; set; }
    [VectorStoreRecordData]
    public string[]? NullableStringArray { get; set; }
#pragma warning restore CA1819 // Properties should not return arrays

    [VectorStoreRecordData]
    public List<string> StringList { get; set; }
    [VectorStoreRecordData]
    public List<string>? NullableStringList { get; set; }

    [VectorStoreRecordVector(Dimensions: 8, DistanceFunction = DistanceFunction.DotProductSimilarity)]
    public ReadOnlyMemory<float>? Embedding { get; set; }

    internal void AssertEqual(PineconeAllTypes other)
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
        Assert.Equal(this.StringArray, other.StringArray);
        Assert.Equal(this.NullableStringArray, other.NullableStringArray);
        Assert.Equal(this.StringList, other.StringList);
        Assert.Equal(this.NullableStringList, other.NullableStringList);
        Assert.Equal(this.Embedding!.Value.ToArray(), other.Embedding!.Value.ToArray());
    }

    internal static VectorStoreRecordDefinition GetRecordDefinition()
        => new()
        {
            Properties =
            [
                new VectorStoreRecordKeyProperty(nameof(PineconeAllTypes.Id), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.BoolProperty), typeof(bool)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableBoolProperty), typeof(bool?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.StringProperty), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableStringProperty), typeof(string)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.IntProperty), typeof(int)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableIntProperty), typeof(int?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.LongProperty), typeof(long)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableLongProperty), typeof(long?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.FloatProperty), typeof(float)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableFloatProperty), typeof(float?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.DoubleProperty), typeof(double)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableDoubleProperty), typeof(double?)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.StringArray), typeof(string[])),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableStringArray), typeof(string[])),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.StringList), typeof(List<string>)),
                new VectorStoreRecordDataProperty(nameof(PineconeAllTypes.NullableStringList), typeof(List<string?>)),
                new VectorStoreRecordVectorProperty(nameof(PineconeAllTypes.Embedding), typeof(ReadOnlyMemory<float>?), 8) { DistanceFunction = Microsoft.Extensions.VectorData.DistanceFunction.DotProductSimilarity }
            ]
        };
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
