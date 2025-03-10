// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorDataSpecificationTests.Models;

/// <summary>
/// This class represents bare minimum that each connector should support:
/// a key, int, string and an embedding.
/// </summary>
/// <typeparam name="TKey">TKey is a generic parameter because different connectors support different key types.</typeparam>
public sealed class SimpleModel<TKey>
{
    [VectorStoreRecordKey(StoragePropertyName = "key")]
    public TKey? Id { get; set; }

    [VectorStoreRecordData(StoragePropertyName = "text")]
    public string? Text { get; set; }

    [VectorStoreRecordData(StoragePropertyName = "number")]
    public int Number { get; set; }

    [VectorStoreRecordVector(Dimensions: 10, StoragePropertyName = "embedding")]
    public ReadOnlyMemory<float> Floats { get; set; }
}
