// Copyright (c) Microsoft. All rights reserved.

using Qdrant.ConformanceTests.Support;
using VectorData.ConformanceTests.ModelTests;
using VectorData.ConformanceTests.Support;
using Xunit;

namespace Qdrant.ConformanceTests.ModelTests;

public class QdrantDynamicModelTests_NamedVectors(QdrantDynamicModelTests_NamedVectors.Fixture fixture)
    : DynamicModelTests<ulong>(fixture), IClassFixture<QdrantDynamicModelTests_NamedVectors.Fixture>
{
    public override async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        var exception = await Assert.ThrowsAsync<NotSupportedException>(base.GetAsync_with_filter_and_multiple_OrderBys);

        Assert.Equal("Qdrant does not support ordering by more than one property.", exception.Message);
    }

    public new class Fixture : DynamicModelTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.NamedVectorsInstance;
    }
}

public class QdrantDynamicModelTests_UnnamedVector(QdrantDynamicModelTests_UnnamedVector.Fixture fixture)
    : DynamicModelTests<ulong>(fixture), IClassFixture<QdrantDynamicModelTests_UnnamedVector.Fixture>
{
    public override async Task GetAsync_with_filter_and_multiple_OrderBys()
    {
        var exception = await Assert.ThrowsAsync<NotSupportedException>(base.GetAsync_with_filter_and_multiple_OrderBys);

        Assert.Equal("Qdrant does not support ordering by more than one property.", exception.Message);
    }

    public new class Fixture : DynamicModelTests<ulong>.Fixture
    {
        public override TestStore TestStore => QdrantTestStore.UnnamedVectorInstance;
    }
}
