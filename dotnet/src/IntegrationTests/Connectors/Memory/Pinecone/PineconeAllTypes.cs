// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Collections.Generic;
using Microsoft.SemanticKernel.Data;

namespace SemanticKernel.IntegrationTests.Connectors.Memory.Pinecone;

#pragma warning disable CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
public record PineconeAllTypes()
#pragma warning restore CS8618 // Non-nullable field must contain a non-null value when exiting constructor. Consider adding the 'required' modifier or declaring as nullable.
{
    [VectorStoreRecordKey]
    public string Id { get; init; }

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
    [VectorStoreRecordData]
    public decimal DecimalProperty { get; set; }
    [VectorStoreRecordData]
    public decimal? NullableDecimalProperty { get; set; }

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

    [VectorStoreRecordData]
    public IReadOnlyCollection<string> Collection { get; set; }
    [VectorStoreRecordData]
    public IEnumerable<string> Enumerable { get; set; }

    [VectorStoreRecordVector(Dimensions: 8, IndexKind: null, DistanceFunction: DistanceFunction.DotProductSimilarity)]
    public ReadOnlyMemory<float>? Embedding { get; set; }
}
