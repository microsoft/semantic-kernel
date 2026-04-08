// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;

namespace VectorData.ConformanceTests.Support;

public abstract class TestRecord<TKey>
{
    [VectorStoreKey]
    public TKey Key { get; set; } = default!;
}
