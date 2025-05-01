// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Xunit;

namespace PineconeIntegrationTests.Support;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
public record PineconeAllTypes()
{
    [VectorStoreKeyProperty]
    public string Id { get; set; }

    [VectorStoreDataProperty]
    public bool BoolProperty { get; set; }
    [VectorStoreDataProperty]
    public bool? NullableBoolProperty { get; set; }
    [VectorStoreDataProperty]
    public string StringProperty { get; set; }
    [VectorStoreDataProperty]
    public string? NullableStringProperty { get; set; }
    [VectorStoreDataProperty]
    public int IntProperty { get; set; }
    [VectorStoreDataProperty]
    public int? NullableIntProperty { get; set; }
    [VectorStoreDataProperty]
    public long LongProperty { get; set; }
    [VectorStoreDataProperty]
    public long? NullableLongProperty { get; set; }
    [VectorStoreDataProperty]
    public float FloatProperty { get; set; }
    [VectorStoreDataProperty]
    public float? NullableFloatProperty { get; set; }
    [VectorStoreDataProperty]
    public double DoubleProperty { get; set; }
    [VectorStoreDataProperty]
    public double? NullableDoubleProperty { get; set; }

#pragma warning disable CA1819 // Properties should not return arrays
    [VectorStoreDataProperty]
    public string[] StringArray { get; set; }
    [VectorStoreDataProperty]
    public string[]? NullableStringArray { get; set; }
#pragma warning restore CA1819 // Properties should not return arrays

    [VectorStoreDataProperty]
    public List<string> StringList { get; set; }
    [VectorStoreDataProperty]
    public List<string>? NullableStringList { get; set; }

    [VectorStoreVectorProperty(Dimensions: 8, DistanceFunction = DistanceFunction.DotProductSimilarity)]
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
                new VectorStoreKeyProperty(nameof(PineconeAllTypes.Id), typeof(string)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.BoolProperty), typeof(bool)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableBoolProperty), typeof(bool?)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.StringProperty), typeof(string)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableStringProperty), typeof(string)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.IntProperty), typeof(int)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableIntProperty), typeof(int?)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.LongProperty), typeof(long)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableLongProperty), typeof(long?)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.FloatProperty), typeof(float)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableFloatProperty), typeof(float?)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.DoubleProperty), typeof(double)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableDoubleProperty), typeof(double?)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.StringArray), typeof(string[])),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableStringArray), typeof(string[])),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.StringList), typeof(List<string>)),
                new VectorStoreDataProperty(nameof(PineconeAllTypes.NullableStringList), typeof(List<string?>)),
                new VectorStoreVectorProperty(nameof(PineconeAllTypes.Embedding), typeof(ReadOnlyMemory<float>?), 8) { DistanceFunction = Microsoft.Extensions.VectorData.DistanceFunction.DotProductSimilarity }
            ]
        };
}
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
