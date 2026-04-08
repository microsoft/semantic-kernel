// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests.ModelTests;

public class QdrantBasicModelTests(QdrantBasicModelTests.Fixture fixture)
    : BasicModelTests<ulong>(fixture), IClassFixture<QdrantBasicModelTests.Fixture>
{
    public override async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        var exception = await Assert.ThrowsAsync<NotSupportedException>(base.GetAsync_with_filter_and_multiple_OrderBys);

        Assert.Equal("Qdrant does not support ordering by more than one property.", exception.Message);
    }

    public new class Fixture : BasicModelTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}
