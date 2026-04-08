// Copyright (c) Microsoft. All rights reserved.

using VectorData.ConformanceTests;
using VectorData.ConformanceTests.Support;
using Weaviate.ConformanceTests.Support;
using Xunit;

namespace Weaviate.ConformanceTests;

public class WeaviateDistanceFunctionTests(WeaviateDistanceFunctionTests.Fixture fixture)
    : DistanceFunctionTests<Guid>(fixture), IClassFixture<WeaviateDistanceFunctionTests.Fixture>
{
    public override Task CosineSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.CosineSimilarity);
    public override Task DotProductSimilarity() => Assert.ThrowsAsync<NotSupportedException>(base.DotProductSimilarity);
    public override Task EuclideanDistance() => Assert.ThrowsAsync<NotSupportedException>(base.EuclideanDistance);

    public new class Fixture() : DistanceFunctionTests<Guid>.Fixture
    {
        public override TestStore TestStore => WeaviateTestStore.NamedVectorsInstance;
    }
}
