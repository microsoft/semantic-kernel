// Copyright (c) Microsoft. All rights reserved.

using Microsoft.Extensions.VectorData;
using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using VectorData.ConformanceTests.Xunit;
using Xunit;

namespace Qdrant.ConformanceTests;

public class QdrantIndexKindTests(QdrantIndexKindTests.Fixture fixture)
    : IndexKindTests<ulong>(fixture), IClassFixture<QdrantIndexKindTests.Fixture>
{
    // Qdrant does not support index-less searching
    public override Task Flat() => Assert.ThrowsAsync<NotSupportedException>(base.Flat);

    [ConditionalFact]
    public virtual Task Hnsw()
        => this.Test(IndexKind.Hnsw);

    public new class Fixture() : IndexKindTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
