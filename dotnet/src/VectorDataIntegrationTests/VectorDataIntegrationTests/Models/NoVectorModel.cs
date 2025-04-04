// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Xunit;

namespace VectorDataSpecificationTests.Models;

/// <summary>
/// This class is for testing databases that support having no vector.
/// Not all DBs support this.
/// </summary>
/// <typeparam name="TKey">TKey is a generic parameter because different connectors support different key types.</typeparam>
public sealed class NoVectorModel<TKey>
{
    public const int DimensionCount = 3;

    [VectorStoreRecordKey(StoragePropertyName = "key")]
    public TKey Id { get; set; } = default!;

    [VectorStoreRecordData(StoragePropertyName = "text")]
    public string? Text { get; set; }

    public void AssertEqual(NoVectorModel<TKey>? other)
    {
        Assert.NotNull(other);
        Assert.Equal(this.Id, other.Id);
        Assert.Equal(this.Text, other.Text);
    }
}
