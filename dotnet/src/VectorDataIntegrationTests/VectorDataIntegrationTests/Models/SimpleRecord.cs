// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorDataSpecificationTests.Models;

/// <summary>
/// This class represents bare minimum that each connector should support:
/// a key, int, string and an embedding.
/// </summary>
/// <typeparam name="TKey">TKey is a generic parameter because different connectors support different key types.</typeparam>
public sealed class SimpleRecord<TKey>
{
    public const int DimensionCount = 3;

    [VectorStoreRecordKey(StoragePropertyName = "key")]
    public TKey Id { get; set; } = default!;

    [VectorStoreRecordData(StoragePropertyName = "text")]
    public string? Text { get; set; }

    [VectorStoreRecordData(StoragePropertyName = "number")]
    public int Number { get; set; }

    [VectorStoreRecordVector(Dimensions: DimensionCount, StoragePropertyName = "embedding")]
    public ReadOnlyMemory<float> Floats { get; set; }

    public void AssertEqual(SimpleRecord<TKey>? other, bool includeVectors, bool compareVectors)
    {
        Assert.NotNull(other);
        Assert.Equal(this.Id, other.Id);
        Assert.Equal(this.Text, other.Text);
        Assert.Equal(this.Number, other.Number);

        if (includeVectors)
        {
            Assert.Equal(this.Floats.Span.Length, other.Floats.Span.Length);

            if (compareVectors)
            {
                Assert.Equal(this.Floats.ToArray(), other.Floats.ToArray());
            }
        }
        else
        {
            Assert.Equal(0, other.Floats.Length);
        }
    }
}
